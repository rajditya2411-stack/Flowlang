"""FlowLang V1 Specification Compliance Tests.

Validates all locked FlowLang V1 features:
- Variable declarations (lit dynamic vs int/flt/str/char/bool static)
- Float division (always producing float)
- pow_() builtin
- String repetition (*) and concatenation (+)
- Operator precedence (C precedence) and associativity (left-to-right)
- Logical operators (and, or, not)
- if / elif / else statements with braces
- while and do-while loops
- for loop with (init; cond; update) and auto-declared loop variable
- dfn functions, parameters, and return
- say() output
- input() and input type wrappers int(), flt(), char(), bool()
- Single-line (#) and block (/* ... */) comments
- Rejection of V2 features (arrays, nil, bitwise)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestFlowLangV1Compliance(unittest.TestCase):

    def run_code(self, source: str, input_handler=None):
        res = execute(source, input_handler=input_handler)
        if res.error:
            self.fail(f"Execution failed with error: {res.error['message']}\nFormatted:\n{res.formatted_error}")
        return res

    # ------------------ 1. Variables & Dynamic Typing ------------------

    def test_lit_dynamic_typing(self):
        code = """
        lit x = 10
        say(x)
        x = "raj"
        say(x)
        x = true
        say(x)
        x = 3.14
        say(x)
        x = 'Z'
        say(x)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["10", "raj", "true", "3.14", "Z"])

    def test_static_typed_declarations_valid(self):
        code = """
        int i = 42
        i = 100
        say(i)

        flt f = 3.14
        f = 2.718
        say(f)

        str s = "hello"
        s = "world"
        say(s)

        char c = 'A'
        c = 'B'
        say(c)

        bool b = true
        b = false
        say(b)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["100", "2.718", "world", "B", "false"])

    def test_static_typed_declarations_mismatch_error(self):
        # int assigned string
        res = execute("int x = 10\nx = \"hello\"")
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

        # flt assigned int
        res = execute("flt z = 2.5\nz = 10")
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

        # str assigned int
        res = execute("str s = \"hello\"\ns = 42")
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

        # bool assigned int
        res = execute("bool flag = true\nflag = 1")
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

        # char assigned multi-char
        res = execute("char c = 'A'\nc = \"too long\"")
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

    def test_assignment_to_undeclared_variable_fails(self):
        res = execute("undeclared = 10")
        self.assertIsNotNone(res.error)
        self.assertIn("Undefined variable", res.error["message"])

    # ------------------ 2. Division Semantics ------------------

    def test_division_always_returns_float(self):
        code = """
        lit a = 20 / 4
        say(a)
        lit b = 20 / 3
        say(b > 6.6 and b < 6.7)
        lit c = 5 / 2
        say(c)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "5.0")
        self.assertEqual(lines[1], "true")
        self.assertEqual(lines[2], "2.5")

    def test_division_by_zero(self):
        res = execute("lit x = 10 / 0")
        self.assertIsNotNone(res.error)
        self.assertIn("Division by zero", res.error["message"])

    def test_modulo_operator(self):
        code = """
        say(10 % 3)
        say(20 % 5)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["1", "0"])

    # ------------------ 3. Power Operation pow_() ------------------

    def test_pow_function(self):
        code = """
        say(pow_(2, 3))
        say(pow_(10, 0))
        say(pow_(2, -1))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["8", "1", "0.5"])

    # ------------------ 4. String Operations ------------------

    def test_string_repetition(self):
        code = """
        lit x = "raj"
        lit a = 2
        say(x * a)
        say(2 * "raj")
        say("abc" * 0)
        """
        res = self.run_code(code)
        lines = res.output.split("\n")
        self.assertEqual(lines, ["rajraj", "rajraj", ""])

    def test_string_multiplication_invalid(self):
        res = execute('lit x = "raj" * -1')
        self.assertIsNotNone(res.error)

        res = execute('lit x = "raj" * 2.5')
        self.assertIsNotNone(res.error)

    def test_string_concatenation(self):
        code = """
        lit x = "raj"
        lit a = 2
        say(x + a)
        say(2 + x)
        say("pi: " + 3.14)
        say("grade: " + 'A')
        say("status: " + true)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["raj2", "2raj", "pi: 3.14", "grade: A", "status: true"])

    def test_invalid_string_arithmetic(self):
        res = execute('"raj" - 2')
        self.assertIsNotNone(res.error)

        res = execute('"raj" / 2')
        self.assertIsNotNone(res.error)

    # ------------------ 5. C Precedence & Associativity ------------------

    def test_c_operator_precedence(self):
        code = """
        say(2 + 3 * 4)
        say(3 * 4 + 2)
        say(10 - 2 * 3)
        say(20 + 10 / 2)
        say(10 > 5 and 3 < 1)
        say(10 > 5 or 3 < 1)
        say(true or false and false)
        say(not false and true)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "14")
        self.assertEqual(lines[1], "14")
        self.assertEqual(lines[2], "4")
        self.assertEqual(lines[3], "25.0")
        self.assertEqual(lines[4], "false")
        self.assertEqual(lines[5], "true")
        self.assertEqual(lines[6], "true")
        self.assertEqual(lines[7], "true")

    def test_left_to_right_associativity(self):
        code = """
        say(10 - 3 - 2)
        say(20 / 4 * 2)
        say(100 / 10 / 2)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "5")
        self.assertEqual(lines[1], "10.0")
        self.assertEqual(lines[2], "5.0")

    # ------------------ 6. Comparisons & Logical Operators ------------------

    def test_comparisons_and_logical(self):
        code = """
        lit age = 25
        if age > 18 and age < 60 {
            say("valid")
        }

        lit x = 10
        if x == 10 or x == 20 {
            say("matched")
        }

        lit active = false
        if not active {
            say("inactive")
        }
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["valid", "matched", "inactive"])

    # ------------------ 7. Control Flow (if/elif/else, while, do-while, for) ------------------

    def test_if_elif_else(self):
        code = """
        dfn check(val) {
            if val > 10 {
                say("big")
            } elif val == 10 {
                say("equal")
            } else {
                say("small")
            }
        }
        check(15)
        check(10)
        check(5)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["big", "equal", "small"])

    def test_while_loop(self):
        code = """
        lit i = 1
        while i <= 4 {
            say(i)
            i = i + 1
        }
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["1", "2", "3", "4"])

    def test_do_while_loop(self):
        code = """
        lit i = 1
        do {
            say(i)
            i = i + 1
        } while i <= 3

        # Runs at least once even when condition initially false
        lit j = 10
        do {
            say("executed once")
            j = j + 1
        } while j < 5
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["1", "2", "3", "executed once"])

    def test_for_loop(self):
        code = """
        for i in (1; i <= 5; i = i + 2) {
            say(i)
        }
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["1", "3", "5"])

    def test_for_loop_nested(self):
        code = """
        for i in (1; i <= 3; i = i + 1) {
            if i % 2 != 0 {
                say("odd: " + i)
            } else {
                say("even: " + i)
            }
        }
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["odd: 1", "even: 2", "odd: 3"])

    # ------------------ 8. Functions (dfn, return) ------------------

    def test_function_declaration_and_return(self):
        code = """
        dfn add(a, b) {
            return a + b
        }
        lit result = add(10, 20)
        say(result)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "30")

    def test_function_recursion(self):
        code = """
        dfn factorial(n) {
            if n <= 1 {
                return 1
            }
            return n * factorial(n - 1)
        }
        say(factorial(5))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "120")

    # ------------------ 9. Input & Output ------------------

    def test_say_output(self):
        code = """
        say("Hello FlowLang")
        say("a", 10, 3.14, true, 'X')
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["Hello FlowLang", "a 10 3.14 true X"])

    def test_print_is_not_supported(self):
        res = execute('print("hello")')
        self.assertIsNotNone(res.error)
        self.assertIn("Undefined variable 'print'", res.error["message"])

    def test_input_handling(self):
        inputs = iter(["Raj", "42", "3.14", "A", "true"])

        def fake_input(prompt=""):
            return next(inputs)

        code = """
        str name = input("Enter name: ")
        int age = int(input())
        flt weight = flt(input())
        char grade = char(input())
        bool active = bool(input())

        say("name:", name)
        say("age:", age + 1)
        say("weight:", weight + 0.5)
        say("grade:", grade)
        say("active:", active)
        """
        res = self.run_code(code, input_handler=fake_input)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, [
            "name: Raj",
            "age: 43",
            "weight: 3.64",
            "grade: A",
            "active: true"
        ])

    # ------------------ 10. Comments ------------------

    def test_comments(self):
        code = """
        # This is a single line comment
        lit x = 10 # inline comment

        /* This is a
           multi-line
           block comment */
        lit y = x + 5 /* another block comment */
        say(y)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "15")

    def test_unterminated_block_comment(self):
        res = execute("/* unclosed comment")
        self.assertIsNotNone(res.error)
        self.assertIn("Unterminated block comment", res.error["message"])

    # ------------------ 11. V2 Features Explicitly Excluded ------------------

    def test_no_arrays_in_v1(self):
        res = execute("lit arr = [1, 2, 3]")
        self.assertIsNotNone(res.error)

    def test_no_nil_in_v1(self):
        res = execute("lit n = nil")
        self.assertIsNotNone(res.error)

    def test_no_bitwise_operators_in_v1(self):
        res = execute("lit x = 5 & 3")
        self.assertIsNotNone(res.error)

        res = execute("lit x = 5 | 3")
        self.assertIsNotNone(res.error)


if __name__ == "__main__":
    unittest.main()

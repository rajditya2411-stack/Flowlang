"""Tests for FlowLang V2 Richer Type System & Explicit Type Conversions."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestFlowLangV2Types(unittest.TestCase):
    """Verifies all aspects of FlowLang V2 Richer Type System specification."""

    def run_code(self, source: str):
        res = execute(source)
        if res.error:
            self.fail(f"Execution failed: {res.error['message']}\nFormatted:\n{res.formatted_error}")
        return res

    # ------------------ 1. Static Variable Typing & Constraints ------------------

    def test_typed_variable_declarations_valid(self):
        code = """
        int a = 42
        flt b = 3.14
        str c = "hello"
        char d = 'Z'
        bool e = true
        list f = [1, 2, 3]
        brack g = (1, 2, 3)
        say(a, b, c, d, e, len_(f), len_(g))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "42 3.14 hello Z true 3 3")

    def test_static_type_mismatch_declarations(self):
        # int cannot accept float or string or bool
        res = execute("int x = 10.5")
        self.assertIsNotNone(res.error)
        res = execute('int x = "10"')
        self.assertIsNotNone(res.error)
        res = execute("int x = true")
        self.assertIsNotNone(res.error)

        # flt cannot accept int or string
        res = execute("flt x = 10")
        self.assertIsNotNone(res.error)
        res = execute('flt x = "3.14"')
        self.assertIsNotNone(res.error)

        # bool cannot accept int or string
        res = execute("bool x = 1")
        self.assertIsNotNone(res.error)
        res = execute("bool x = 0")
        self.assertIsNotNone(res.error)
        res = execute('bool x = "true"')
        self.assertIsNotNone(res.error)

        # char cannot accept string of length > 1
        res = execute('char c = "ab"')
        self.assertIsNotNone(res.error)

        # list cannot accept brack
        res = execute("list l = (1, 2)")
        self.assertIsNotNone(res.error)

        # brack cannot accept list
        res = execute("brack b = [1, 2]")
        self.assertIsNotNone(res.error)

    def test_static_type_mismatch_assignment(self):
        code = """
        mut int x = 10
        x = 20
        """
        self.assertIsNone(execute(code).error)

        # Reassigning wrong type
        res = execute("mut int x = 10\nx = 10.5")
        self.assertIsNotNone(res.error)
        res = execute('mut int x = 10\nx = "hello"')
        self.assertIsNotNone(res.error)

        res = execute("mut flt y = 3.14\ny = 10")
        self.assertIsNotNone(res.error)

        res = execute("mut bool b = true\nb = 1")
        self.assertIsNotNone(res.error)

    # ------------------ 2. none Runtime Value Rules ------------------

    def test_none_variable_declaration_fails(self):
        res = execute("none x = 10")
        self.assertIsNotNone(res.error)
        self.assertIn("none", res.error["message"].lower())

    def test_none_as_variable_name_fails(self):
        res = execute("int none = 10")
        self.assertIsNotNone(res.error)
        self.assertIn("none", res.error["message"].lower())

    def test_none_assignment_fails(self):
        res = execute("none = 10")
        self.assertIsNotNone(res.error)

    def test_lit_holds_none(self):
        code = """
        lit x = none
        say(x)
        say(x == none)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["none", "true"])

    # ------------------ 3. Explicit Numeric Conversions & Rounding ------------------

    def test_int_rounding_rule(self):
        code = """
        say(int_(10.5))
        say(int_(10.6))
        say(int_(10.1))
        say(int_(10.9))
        say(int_(-10.5))
        say(int_(-10.6))
        say(int_(-10.1))
        say(int_(-10.9))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["10", "11", "10", "11", "-10", "-11", "-10", "-11"])

    def test_int_string_conversions(self):
        code = """
        say(int_("10"))
        say(int_("10.5"))
        say(int_("10.6"))
        say(int_("-10.5"))
        say(int_("-10.6"))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["10", "10", "11", "-10", "-11"])

    def test_int_rejections(self):
        # bool to int rejected
        res = execute("int_(true)")
        self.assertIsNotNone(res.error)
        res = execute("int_(false)")
        self.assertIsNotNone(res.error)

        # char to int rejected (deferred to V3)
        res = execute("int_('A')")
        self.assertIsNotNone(res.error)

    def test_flt_conversions(self):
        code = """
        say(flt_(10))
        say(flt_("3.14"))
        say(flt_("-42.5"))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["10.0", "3.14", "-42.5"])

        res = execute("flt_(true)")
        self.assertIsNotNone(res.error)
        res = execute("flt_('A')")
        self.assertIsNotNone(res.error)

    # ------------------ 4. Other Type Conversions ------------------

    def test_str_conversion(self):
        code = """
        say(str_(10))
        say(str_(3.14))
        say(str_(true))
        say(str_('A'))
        say(str_(none))
        say(str_([1, 2]))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["10", "3.14", "true", "A", "none", "[1, 2]"])

    def test_char_conversion(self):
        code = """
        char c = 'A'
        say(str_(c))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "A")

        # char_() is completely removed
        res1 = execute('char_("hello")')
        self.assertIsNotNone(res1.error)

        # char -> int is invalid
        res2 = execute("char c = 'A'\nint_(c)")
        self.assertIsNotNone(res2.error)

        # char -> flt is invalid
        res3 = execute("char c = 'A'\nflt_(c)")
        self.assertIsNotNone(res3.error)

    def test_bool_conversion(self):
        # Strict boolean conversion: numbers cannot be converted to bool
        res1 = execute("bool_(1)")
        self.assertIsNotNone(res1.error)
        res0 = execute("bool_(0)")
        self.assertIsNotNone(res0.error)

        code = """
        say(bool_("true"))
        say(bool_("false"))
        say(bool_(true))
        say(bool_(false))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["true", "false", "true", "false"])

    # ------------------ 5. Strict Boolean Isolation ------------------

    def test_boolean_isolation_arithmetic(self):
        res = execute("true + 5")
        self.assertIsNotNone(res.error)

        res = execute("5 + true")
        self.assertIsNotNone(res.error)

        res = execute("true * 3")
        self.assertIsNotNone(res.error)

        res = execute("true - 1")
        self.assertIsNotNone(res.error)

        res = execute("true / 2")
        self.assertIsNotNone(res.error)

    def test_boolean_isolation_string_concat(self):
        res = execute('"val: " + true')
        self.assertIsNotNone(res.error)

        res = execute('true + " is boolean"')
        self.assertIsNotNone(res.error)

        # Explicit conversion works
        code = 'say("val: " + str_(true))'
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "val: true")

    def test_boolean_isolation_equality(self):
        res = execute("true == 1")
        self.assertIsNotNone(res.error)

        res = execute("1 == true")
        self.assertIsNotNone(res.error)

        res = execute("false == 0")
        self.assertIsNotNone(res.error)

    # ------------------ 6. Strict Type Equality (==, !=) ------------------

    def test_strict_type_equality_errors(self):
        res = execute('10 == "10"')
        self.assertIsNotNone(res.error)

        res = execute('10 != "10"')
        self.assertIsNotNone(res.error)

        res = execute("[1, 2] == (1, 2)")
        self.assertIsNotNone(res.error)

        res = execute("none == 10")
        self.assertIsNotNone(res.error)

        res = execute('\'a\' == "a"')
        self.assertIsNotNone(res.error)

    def test_compatible_type_equality(self):
        code = """
        say(10 == 10.0)
        say(10 != 10.5)
        say(none == none)
        say(none != none)
        say('a' == 'a')
        say('a' != 'b')
        say("hello" == "hello")
        say(true == true)
        say(true != false)
        say([1, 2] == [1, 2])
        say((1, 2) == (1, 2))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, [
            "true",
            "true",
            "true",
            "false",
            "true",
            "true",
            "true",
            "true",
            "true",
            "true",
            "true",
        ])

    # ------------------ 7. Lit Rules & Constraints ------------------

    def test_lit_carrier_types(self):
        code = """
        lit a = 10
        lit b = "hello"
        lit c = true
        lit d = (1, 2, 3)
        say(a, b, c, len_(d))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "10 hello true 3")

    def test_lit_cannot_hold_mutable_list(self):
        res = execute("lit x = [1, 2, 3]")
        self.assertIsNotNone(res.error)
        self.assertIn("mutable list", res.error["message"])

        res = execute("list nums = [1, 2, 3]\nlit x = nums")
        self.assertIsNotNone(res.error)

        # Must freeze first
        code = """
        lit x = freeze_([1, 2, 3])
        say(x)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "(1, 2, 3)")

    def test_lit_direct_assignment_to_static_var_fails(self):
        # lit x = 10; int y = x -> fails
        res = execute("lit x = 10\nint y = x")
        self.assertIsNotNone(res.error)
        self.assertIn("Cannot directly assign 'lit' variable", res.error["message"])

        # With explicit conversion -> works
        code = """
        lit x = 10
        int y = int_(x)
        say(y)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "10")

        # In assignment statement too
        res = execute("lit x = 10\nmut int y = 0\ny = x")
        self.assertIsNotNone(res.error)

        code = """
        lit x = 10
        mut int y = 0
        y = int_(x)
        say(y)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "10")

    def test_lit_operations_use_underlying_values(self):
        code = """
        lit a = 10
        lit b = 20
        say(a + b)
        say(a == b)
        say(a != b)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["30", "false", "true"])

        # Comparing lit directly with concrete typed variable fails without explicit conversion
        res = execute('lit a = 10\nint b = 10\nsay(a == b)')
        self.assertIsNotNone(res.error)

        # Comparing lit with incompatible type still fails
        res = execute('lit a = 10\nlit b = "10"\nsay(a == b)')
        self.assertIsNotNone(res.error)

    # ------------------ 8. type_() Built-in ------------------

    def test_type_builtin_variables_vs_expressions(self):
        code = """
        dfn sample_fn() -> lit { return 0; }
        lit x = 10
        int y = 20
        flt z = 3.14
        str s = "hello"
        char c = 'a'
        bool b = true
        list l = [1, 2]
        brack bk = (1, 2)
        func fn = sample_fn
        lit n = none

        # Variable identifier -> declared type
        say(type_(x))
        say(type_(y))
        say(type_(z))
        say(type_(s))
        say(type_(c))
        say(type_(b))
        say(type_(l))
        say(type_(bk))
        say(type_(fn))
        say(type_(n))

        # Expressions -> runtime value type
        say(type_(10 + 2.5))
        say(type_(10))
        say(type_("abc"))
        say(type_('x'))
        say(type_(true))
        say(type_([1, 2, 3]))
        say(type_((1, 2, 3)))
        say(type_(none))
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, [
            "lit",
            "int",
            "flt",
            "str",
            "char",
            "bool",
            "list",
            "brack",
            "func",
            "lit",
            # Expressions:
            "flt",
            "int",
            "str",
            "char",
            "bool",
            "list",
            "brack",
            "none",
        ])

    # ------------------ 9. Function Declaration Rules ------------------

    def test_function_mandatory_return_type(self):
        # Missing -> return_type is syntax error
        res = execute("dfn add(a, b) { return a + b }")
        self.assertIsNotNone(res.error)

        # -> none is invalid return type
        res = execute("dfn add(a, b) -> none { return a + b }")
        self.assertIsNotNone(res.error)

        # Valid declarations
        code = """
        dfn add(a, b) -> int {
            return a + b
        }
        say(add(10, 20))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "30")

    def test_function_return_type_enforcement(self):
        # Returns wrong type
        res = execute("""
        dfn bad() -> int {
            return "not an int"
        }
        bad()
        """)
        self.assertIsNotNone(res.error)

        # Non-lit function missing return statement -> error
        res = execute("""
        dfn missing_ret() -> int {
            say("no return")
        }
        missing_ret()
        """)
        self.assertIsNotNone(res.error)
        self.assertIn("missing return statement", res.error["message"])

        # lit function missing return statement -> OK (returns none)
        code = """
        dfn greet() -> lit {
            say("hello")
        }
        lit res = greet()
        say(res == none)
        """
        res = self.run_code(code)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines, ["hello", "true"])

        # lit function returning mutable list -> fails
        res = execute("""
        dfn returns_list() -> lit {
            return [1, 2, 3]
        }
        returns_list()
        """)
        self.assertIsNotNone(res.error)
        self.assertIn("cannot return a mutable list", res.error["message"])

    def test_function_typed_parameters(self):
        code = """
        dfn typed_fn(int a, str b) -> str {
            return b + str_(a)
        }
        say(typed_fn(42, "num: "))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "num: 42")

        # Passing wrong argument type
        res = execute("""
        dfn typed_fn(int a, str b) -> str {
            return b + str_(a)
        }
        typed_fn("wrong", "str")
        """)
        self.assertIsNotNone(res.error)

        # Passing mutable list to lit parameter fails
        res = execute("""
        dfn lit_fn(lit x) -> lit {
            return x
        }
        lit_fn([1, 2, 3])
        """)
        self.assertIsNotNone(res.error)
        self.assertIn("cannot accept a mutable list", res.error["message"])


if __name__ == "__main__":
    unittest.main()

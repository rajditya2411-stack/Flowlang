"""FlowLang V2 Hardened Compliance Test Suite.

Validates all 60 finalized edge-case rules from the V2 audit:
- Integer division // and float division /
- Division by zero for / and //
- C-style remainder %
- 32-bit signed integer overflow on +, -, *, //, negation, pow_
- Single line comments (# only) and rejection of unary +
- Rejection of chained comparisons (a < b < c)
- Strict booleans in logical operators (and, or, not) and loop/if conditions
- Character restrictions: rejection of numeric chars, char arithmetic, and char ordering
- String multiplication (* 0 -> "", * -1 -> error, * flt -> error)
- String indexing with negative bounds and out-of-range checks
- Deep freeze_() of nested collections
- Incompatible collection equality rejection
- Dict key strict typing (int vs flt)
- Block scoping, shadowing, and function return enforcement
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestV2HardenedCompliance(unittest.TestCase):

    def run_code(self, source: str):
        res = execute(source)
        if res.error:
            self.fail(f"Execution failed: {res.error['message']}\nFormatted:\n{res.formatted_error}")
        return res

    # ------------------ 1. Division & Modulo ------------------

    def test_float_and_integer_division(self):
        # / always produces flt
        res1 = self.run_code("say(20 / 4)")
        self.assertEqual(res1.output.strip(), "5.0")

        # // produces integer quotient
        res2 = self.run_code("say(20 // 4)")
        self.assertEqual(res2.output.strip(), "5")

        res3 = self.run_code("say(7 // 3)")
        self.assertEqual(res3.output.strip(), "2")

        # Negative operands for //
        res4 = self.run_code("say(-7 // 3); say(7 // -3); say(-7 // -3)")
        self.assertEqual(res4.output.strip().split("\n"), ["-2", "-2", "2"])

        # // strictly for integers
        res_flt = execute("10.5 // 2")
        self.assertIsNotNone(res_flt.error)

        # Division by zero
        res_zero1 = execute("10 / 0")
        self.assertIsNotNone(res_zero1.error)
        res_zero2 = execute("10 // 0")
        self.assertIsNotNone(res_zero2.error)

    def test_c_style_modulo(self):
        code = """
        say(-7 % 3)
        say(7 % -3)
        say(-7 % -3)
        say(7 % 3)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["-1", "1", "-1", "1"])

        # % with floats is an error
        res_flt = execute("10.5 % 3.0")
        self.assertIsNotNone(res_flt.error)

        # % by zero is an error
        res_zero = execute("10 % 0")
        self.assertIsNotNone(res_zero.error)

    # ------------------ 2. 32-Bit Signed Integer Overflow ------------------

    def test_integer_overflow(self):
        # Addition overflow
        res_add = execute("int x = 2147483647; int y = x + 1;")
        self.assertIsNotNone(res_add.error)
        self.assertIn("Integer overflow", res_add.error["message"])

        # Subtraction overflow
        res_sub = execute("int x = -2147483648; int y = x - 1;")
        self.assertIsNotNone(res_sub.error)
        self.assertIn("Integer overflow", res_sub.error["message"])

        # Multiplication overflow
        res_mul = execute("int x = 2147483647; int y = x * 2;")
        self.assertIsNotNone(res_mul.error)
        self.assertIn("Integer overflow", res_mul.error["message"])

        # Unary negation overflow: -(-2147483648)
        res_neg = execute("int x = -2147483648; int y = -x;")
        self.assertIsNotNone(res_neg.error)
        self.assertIn("Integer overflow", res_neg.error["message"])

        # Integer division overflow: -2147483648 // -1
        res_div = execute("int x = -2147483648; int y = x // -1;")
        self.assertIsNotNone(res_div.error)
        self.assertIn("Integer overflow", res_div.error["message"])

        # pow_() overflow
        res_pow = execute("int x = pow_(2, 31);")
        self.assertIsNotNone(res_pow.error)
        self.assertIn("Integer overflow", res_pow.error["message"])

        # Valid boundary calculation succeeds
        res_ok = self.run_code("int x = 2147483646 + 1; say(x);")
        self.assertEqual(res_ok.output.strip(), "2147483647")

    # ------------------ 3. Comments, Unary +, Chained Comparisons ------------------

    def test_comments_and_unary_plus(self):
        # # is single-line comment
        res = self.run_code("""
        # This is a comment
        int x = 10; # inline comment
        say(x);
        """)
        self.assertEqual(res.output.strip(), "10")

        # Unary + is rejected
        res_unary_plus = execute("int x = +5;")
        self.assertIsNotNone(res_unary_plus.error)
        self.assertIn("Unary '+' is not supported", res_unary_plus.error["message"])

    def test_chained_comparisons_rejected(self):
        res1 = execute("bool b = 1 < 2 < 3;")
        self.assertIsNotNone(res1.error)
        self.assertIn("Chained comparisons are not supported", res1.error["message"])

        res2 = execute("bool b = 1 == 2 == 3;")
        self.assertIsNotNone(res2.error)
        self.assertIn("Chained comparisons are not supported", res2.error["message"])

        # Proper syntax with 'and' succeeds
        res_ok = self.run_code("bool b = 1 < 2 and 2 < 3; say(b);")
        self.assertEqual(res_ok.output.strip(), "true")

    # ------------------ 4. Strict Booleans & Conditions ------------------

    def test_strict_boolean_operands(self):
        # Logical operators require strict bool operands
        self.assertIsNotNone(execute("1 and true").error)
        self.assertIsNotNone(execute('"hello" or false').error)
        self.assertIsNotNone(execute("not 10").error)
        self.assertIsNotNone(execute("not none").error)

        # Short circuiting
        res_sc1 = self.run_code("say(false and (1 / 0 == 0))")
        self.assertEqual(res_sc1.output.strip(), "false")

        res_sc2 = self.run_code("say(true or (1 / 0 == 0))")
        self.assertEqual(res_sc2.output.strip(), "true")

    def test_strict_conditions(self):
        # Conditionals require strict bool
        self.assertIsNotNone(execute("if 1 { say(1); }").error)
        self.assertIsNotNone(execute('if "yes" { say(1); }').error)
        self.assertIsNotNone(execute("lit x = none; if x { say(1); }").error)
        self.assertIsNotNone(execute("while 10 { break; }").error)
        self.assertIsNotNone(execute('do { } while ("hello");').error)

    # ------------------ 5. Characters ------------------

    def test_character_restrictions(self):
        # Numeric char literals are rejected in V2
        res_digit = execute("char c = '1';")
        self.assertIsNotNone(res_digit.error)
        self.assertIn("Numeric character", res_digit.error["message"])

        # Character arithmetic is invalid in V2
        res_arith = execute("char c = 'a'; say(c + 1);")
        self.assertIsNotNone(res_arith.error)
        self.assertIn("Character arithmetic is not supported", res_arith.error["message"])

        # Character ordering is invalid in V2
        res_ord = execute("say('a' < 'b');")
        self.assertIsNotNone(res_ord.error)
        self.assertIn("Comparison operator", res_ord.error["message"])

        # Character equality and string concatenation are supported
        code = """
        char a = 'a';
        char b = 'b';
        say(a == a);
        say(a != b);
        say("char: " + a);
        say(b + " is a letter");
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["true", "true", "char: a", "b is a letter"])

    # ------------------ 6. String Operations ------------------

    def test_string_operations(self):
        # String * 0 returns ""
        res_zero = self.run_code('say("raj" * 0);')
        self.assertEqual(res_zero.output.strip(), "")

        # String * negative integer is error
        res_neg = execute('"raj" * -2')
        self.assertIsNotNone(res_neg.error)

        # String * float is error
        res_flt = execute('"raj" * 2.5')
        self.assertIsNotNone(res_flt.error)

        # String indexing
        code_idx = """
        str s = "hello";
        say(s[0]);
        say(s[-1]);
        """
        res_idx = self.run_code(code_idx)
        self.assertEqual(res_idx.output.strip().split("\n"), ["h", "o"])

        # String indexing out of range
        res_oob = execute('str s = "hi"; say(s[5]);')
        self.assertIsNotNone(res_oob.error)

        # String item assignment is error
        res_assign = execute('str s = "hi"; s[0] = "x";')
        self.assertIsNotNone(res_assign.error)

        # String + collection requires explicit str_()
        res_col = execute('"data: " + (1, 2)')
        self.assertIsNotNone(res_col.error)

    # ------------------ 7. Collections & freeze_() ------------------

    def test_collections_and_deep_freeze(self):
        # Deep freeze nested lists
        code_freeze = """
        list nested = [[1, 2], [3, 4]];
        lit frozen = freeze_(nested);
        say(frozen);
        """
        res = self.run_code(code_freeze)
        self.assertEqual(res.output.strip(), "((1, 2), (3, 4))")

        # Negative index assignment on mutable list
        code_neg = """
        list a = [10, 20];
        a[-1] = 99;
        say(a);
        """
        res_neg = self.run_code(code_neg)
        self.assertEqual(res_neg.output.strip(), "[10, 99]")

        # Out-of-bounds index assignment raises error
        res_oob = execute("list a = [1, 2]; a[10] = 5;")
        self.assertIsNotNone(res_oob.error)

        # Item assignment on immutable brack raises error
        res_brack = execute("brack b = (1, 2); b[0] = 5;")
        self.assertIsNotNone(res_brack.error)

        # Incompatible collection equality raises error
        res_eq = execute("say([1, 2] == (1, 2));")
        self.assertIsNotNone(res_eq.error)

        # Dict key strict typing (1 vs 1.0)
        code_dict = """
        dict d = << 1: "int_key" >>;
        say(d[1]);
        """
        res_dict = self.run_code(code_dict)
        self.assertEqual(res_dict.output.strip(), "int_key")

        res_key_flt = execute('dict d = << 1: "int_key" >>; say(d[1.0]);')
        self.assertIsNotNone(res_key_flt.error)

    # ------------------ 8. Functions, Scoping & Modules ------------------

    def test_functions_and_scopes(self):
        # Missing return statement in typed function raises error
        res_ret = execute("dfn test() -> int { int x = 5; } test();")
        self.assertIsNotNone(res_ret.error)
        self.assertIn("missing return statement", res_ret.error["message"])

        # -> lit function with missing return produces none
        code_lit = """
        dfn test() -> lit { int x = 5; }
        say(test());
        """
        res_lit = self.run_code(code_lit)
        self.assertEqual(res_lit.output.strip(), "none")

        # Returning mutable list from -> lit raises error
        res_mut = execute("dfn test() -> lit { list a = [1, 2]; return a; } test();")
        self.assertIsNotNone(res_mut.error)

        # Passing lit variable directly to typed parameter raises error
        res_param = execute("dfn add(int a, int b) -> int { return a + b; } lit x = 10; add(x, 5);")
        self.assertIsNotNone(res_param.error)
        self.assertIn("Cannot directly pass 'lit' variable", res_param.error["message"])

        # Duplicate function declaration in same scope raises error
        res_dup_fn = execute("dfn foo() -> int { return 1; } dfn foo() -> int { return 2; }")
        self.assertIsNotNone(res_dup_fn.error)
        self.assertIn("already defined in this scope", res_dup_fn.error["message"])

        # Duplicate module import raises error
        res_dup_imp = execute("import flowlib; import flowlib;")
        self.assertIsNotNone(res_dup_imp.error)
        self.assertIn("already been imported", res_dup_imp.error["message"])

        # Block scoping and outer variable mutation
        code_scope = """
        mut int x = 10;
        {
            x = 20;
            int y = 99;
        }
        say(x);
        """
        res_scope = self.run_code(code_scope)
        self.assertEqual(res_scope.output.strip(), "20")

        # For loop variable strictly scoped to loop body
        res_loop_var = execute("for i in 0 -> 3 { say(i); } say(i);")
        self.assertIsNotNone(res_loop_var.error)


if __name__ == "__main__":
    unittest.main()

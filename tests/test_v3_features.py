"""FlowLang V3 Feature Test Suite.

Tests all FlowLang V3 additions:
1. Enums (declaration, member access, opaque representation, strict comparison, int_/str_ conversions, type annotations)
2. Error handling (try, catch, raise, system error interception, block scoping)
3. First-class functions (function type, passing as argument, storing in variables)
4. Duplicate identifier prevention in same scope
5. Nested function definitions & closures
6. Call-stack recursion depth guard
7. Global keyword for explicit global mutation in functions
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute
from flowlang.errors import FlowRuntimeError, ParserError


class TestFlowLangV3Features(unittest.TestCase):

    def run_code(self, source: str):
        result = execute(source)
        if result.error:
            self.fail(f"Execution failed: {result.error['message']}\nFormatted:\n{result.formatted_error}")
        return result

    def expect_error(self, source: str, error_message_substr: str):
        result = execute(source)
        self.assertIsNotNone(result.error, f"Expected error containing '{error_message_substr}', but code succeeded: {result.output}")
        self.assertIn(error_message_substr, result.error["message"])
        return result

    # ==================== 1. Enums ====================

    def test_enum_declaration_and_access(self):
        code = """
        enum Status = << PENDING, ACTIVE, INACTIVE >>
        Status s = Status.PENDING
        say(s)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "Status.PENDING")

    def test_enum_conversions_str_and_int_error(self):
        code = """
        enum Priority = << LOW, MEDIUM, HIGH >>
        Priority p = Priority.MEDIUM
        say(str_(p))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "MEDIUM")

        self.expect_error("""
        enum Priority = << LOW, MEDIUM, HIGH >>
        say(int_(Priority.LOW))
        """, "int_() cannot convert enum to int (enums are opaque in FlowLang)")

    def test_enum_equality_strict(self):
        code = """
        enum Status = << PENDING, ACTIVE >>
        Status s1 = Status.PENDING
        Status s2 = Status.ACTIVE
        Status s3 = Status.PENDING
        say(s1 == s3)
        say(s1 == s2)
        say(s1 != s2)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["true", "false", "true"])

    def test_enum_incompatible_comparison_error(self):
        # Comparing different enum types raises error
        code1 = """
        enum Status = << PENDING, ACTIVE >>
        enum Role = << ADMIN, USER >>
        bool b = (Status.PENDING == Role.ADMIN)
        """
        self.expect_error(code1, "cannot compare incompatible types 'Status' and 'Role'")

        # Comparing enum with int raises error
        code2 = """
        enum Status = << PENDING, ACTIVE >>
        bool b = (Status.PENDING == 0)
        """
        self.expect_error(code2, "cannot compare incompatible types 'Status' and 'int'")

        # Relational comparison (<, >) on enums raises error
        code3 = """
        enum Status = << PENDING, ACTIVE >>
        bool b = (Status.PENDING < Status.ACTIVE)
        """
        self.expect_error(code3, "requires operands of same comparable type")

    def test_enum_type_annotations_in_variables_and_structs(self):
        code = """
        enum Level = << LOW, HIGH >>
        struct Task = << str name, Level lvl >>
        Task t = << "Bugfix", Level.HIGH >>
        say(t.name)
        say(t.lvl)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["Bugfix", "Level.HIGH"])

    def test_enum_type_annotations_in_functions(self):
        code = """
        enum Direction = << NORTH, SOUTH, EAST, WEST >>
        dfn is_north(Direction d) -> bool {
            return d == Direction.NORTH
        }
        say(is_north(Direction.NORTH))
        say(is_north(Direction.SOUTH))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["true", "false"])

    def test_enum_reassignment_with_mut(self):
        code = """
        enum Status = << PENDING, ACTIVE, DONE >>
        mut Status st = Status.PENDING
        st = Status.DONE
        say(st)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "Status.DONE")

    def test_enum_invalid_member_access(self):
        code = """
        enum Status = << PENDING, ACTIVE >>
        Status s = Status.UNKNOWN
        """
        self.expect_error(code, "Enum 'Status' has no member 'UNKNOWN'")

    def test_enum_duplicate_member_definition_error(self):
        code = """
        enum Status = << PENDING, ACTIVE, PENDING >>
        """
        self.expect_error(code, "Duplicate member 'PENDING' in enum 'Status'")

    def test_enum_duplicate_declaration_error(self):
        code = """
        enum Status = << PENDING, ACTIVE >>
        enum Status = << A, B >>
        """
        self.expect_error(code, "Identifier 'Status' is already defined in this scope")

    # ==================== 2. Error Handling (try / catch / raise) ====================

    def test_try_catch_user_raise(self):
        code = """
        try {
            raise "something went wrong"
        } catch (str err) {
            say("Caught: " + err)
        }
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "Caught: something went wrong")

    def test_try_catch_system_error(self):
        code = """
        try {
            int x = 10 // 0
        } catch (str err) {
            say("Handled division: " + err)
        }
        """
        res = self.run_code(code)
        self.assertIn("Handled division: Division by zero", res.output.strip())

    def test_try_catch_index_out_of_bounds(self):
        code = """
        list arr = [1, 2, 3]
        try {
            int val = arr[99]
        } catch (str err) {
            say("Handled bounds: " + err)
        }
        """
        res = self.run_code(code)
        self.assertIn("Handled bounds:", res.output.strip())

    def test_try_catch_error_variable_scoping(self):
        code = """
        try {
            raise "oops"
        } catch (str err) {
            say(err)
        }
        say(err)
        """
        self.expect_error(code, "Undefined variable 'err'")

    def test_try_catch_nested(self):
        code = """
        try {
            try {
                raise "inner error"
            } catch (str e1) {
                say("Catch 1: " + e1)
                raise "outer error"
            }
        } catch (str e2) {
            say("Catch 2: " + e2)
        }
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["Catch 1: inner error", "Catch 2: outer error"])

    # ==================== 3. First-Class Functions ====================

    def test_first_class_function_variable_assignment(self):
        code = """
        dfn double(int x) -> int {
            return x * 2
        }
        func fn = double
        say(fn(21))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "42")

    def test_first_class_function_passing_to_function(self):
        code = """
        dfn add_ten(int x) -> int {
            return x + 10
        }
        dfn apply_fn(func f, int val) -> int {
            return f(val)
        }
        say(apply_fn(add_ten, 5))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "15")

    def test_first_class_function_reassignment(self):
        code = """
        dfn inc(int x) -> int { return x + 1; }
        dfn dec(int x) -> int { return x - 1; }

        mut func f = inc
        say(f(10))
        f = dec
        say(f(10))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip().split("\n"), ["11", "9"])

    def test_lit_cannot_hold_function(self):
        code = """
        dfn inc(int x) -> int { return x + 1; }
        lit f = inc
        """
        self.expect_error(code, "Variable 'f' declared as 'lit' cannot hold a function (use 'func' type)")

    # ==================== 4. Duplicate Identifier Checks ====================

    def test_duplicate_variable_declaration_error(self):
        code = """
        int x = 10
        int x = 20
        """
        self.expect_error(code, "Identifier 'x' is already defined in this scope")

    def test_duplicate_function_declaration_error(self):
        code = """
        dfn foo() -> int { return 1; }
        dfn foo() -> int { return 2; }
        """
        self.expect_error(code, "already defined in this scope")

    def test_function_and_variable_collision_error(self):
        code = """
        dfn bar() -> int { return 1; }
        int bar = 99
        """
        self.expect_error(code, "Identifier 'bar' is already defined in this scope")

    # ==================== 5. Nested Functions & Scopes ====================

    def test_nested_function_definition_and_call(self):
        code = """
        dfn outer(int x) -> int {
            dfn inner(int y) -> int {
                return y * 3
            }
            return inner(x) + 1
        }
        say(outer(4))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "13")

    def test_nested_function_reading_outer_variable(self):
        code = """
        dfn solve(int a, int b) -> int {
            int base = 100
            dfn helper(int x) -> int {
                return base + x
            }
            return helper(a) + helper(b)
        }
        say(solve(5, 10))
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "215")

    # ==================== 6. Recursion Depth Guard ====================

    def test_recursion_depth_guard(self):
        code = """
        dfn infinite_recurse(int n) -> int {
            return infinite_recurse(n + 1)
        }
        infinite_recurse(0)
        """
        self.expect_error(code, "Maximum recursion depth exceeded (1000)")

    # ==================== 7. Global Keyword ====================

    def test_global_variable_read_without_global_keyword(self):
        code = """
        int g = 42
        dfn read_g() -> int {
            return g
        }
        say(read_g())
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "42")

    def test_global_mutation_without_global_keyword_raises_error(self):
        code = """
        mut int g = 10
        dfn mutate_g() -> lit {
            g = 20
        }
        mutate_g()
        """
        self.expect_error(code, "Cannot assign to global variable 'g' without 'global' declaration in function")

    def test_global_mutation_with_global_keyword_succeeds(self):
        code = """
        mut int g = 10
        dfn mutate_g() -> lit {
            global g
            g = 20
        }
        mutate_g()
        say(g)
        """
        res = self.run_code(code)
        self.assertEqual(res.output.strip(), "20")


if __name__ == "__main__":
    unittest.main()

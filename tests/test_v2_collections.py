"""Tests for FlowLang V2 Collections Fundamentals.

Covers:
- List: creation, mutation, indexing, negative indexing, len_, append_, copy independence, iteration, ranged iteration
- Brack: creation, immutability, indexing, len_, listb_, freeze_, iteration, ranged iteration
- Dict: << >> syntax, key types, bool rejection, collection rejection, duplicate key error,
  lookup, update, insert, remove_, len_, keys/values iteration, ranged iteration, copy independence
- Collection Input: bk(input(...)), string vs int parsing without eval, listb_(bk(input(...)))
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestV2List(unittest.TestCase):
    def test_list_creation_and_empty(self):
        res = execute("list nums = [1, 2, 3, 4]\nsay(nums)")
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "[1, 2, 3, 4]")

        res2 = execute("list empty = []\nsay(len_(empty))")
        self.assertIsNone(res2.error)
        self.assertEqual(res2.output.strip(), "0")

    def test_list_mixed_and_nested(self):
        code = """
        list mixed = [10, 3.14, true, 'a', "hello"]
        say(mixed[0], mixed[1], mixed[2], mixed[3], mixed[4])
        list nested = [[1, 2], [3, 4]]
        say(nested[0][0], nested[1][1])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "10 3.14 true a hello")
        self.assertEqual(lines[1], "1 4")

    def test_list_indexing_positive_and_negative(self):
        code = """
        list nums = [10, 20, 30, 40]
        say(nums[0])
        say(nums[2])
        say(nums[-1])
        say(nums[-2])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["10", "30", "40", "30"])

    def test_list_index_out_of_range(self):
        res = execute("list nums = [1, 2]\nsay(nums[5])")
        self.assertIsNotNone(res.error)
        self.assertIn("out of range", res.error["message"])

        res2 = execute("list nums = [1, 2]\nsay(nums[-3])")
        self.assertIsNotNone(res2.error)
        self.assertIn("out of range", res2.error["message"])

    def test_list_index_assignment(self):
        code = """
        list nums = [1, 2, 3, 4]
        nums[1] = 99
        nums[-1] = 400
        say(nums)
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "[1, 99, 3, 400]")

    def test_list_append(self):
        code = """
        list nums = [1, 2, 3]
        append_(nums, 4)
        append_(nums, 50)
        say(nums)
        say(len_(nums))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "[1, 2, 3, 4, 50]")
        self.assertEqual(lines[1], "5")

    def test_list_copy_semantics(self):
        code = """
        list nums = [1, 2, 3, 4]
        list b = nums
        b[1] = 5
        say(b)
        say(nums)
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "[1, 5, 3, 4]")
        self.assertEqual(lines[1], "[1, 2, 3, 4]")

    def test_list_iteration(self):
        code = """
        list nums = [10, 20, 30]
        for i in nums {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["10", "20", "30"])

    def test_list_ranged_iteration_inclusive(self):
        code = """
        list nums = [10, 20, 30, 40, 50, 60, 70, 80, 90]
        for i in nums(2; 8; 2) {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        # Indexes: 2 -> 30, 4 -> 50, 6 -> 70, 8 -> 90
        self.assertEqual(res.output.strip().split("\n"), ["30", "50", "70", "90"])

    def test_list_ranged_iteration_default_step(self):
        code = """
        list nums = [10, 20, 30, 40, 50]
        for i in nums(1; 3) {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        # Indexes 1, 2, 3 -> 20, 30, 40
        self.assertEqual(res.output.strip().split("\n"), ["20", "30", "40"])


class TestV2Brack(unittest.TestCase):
    def test_brack_creation_and_empty(self):
        code = """
        brack nums = (1, 2, 3, 4)
        say(nums)
        brack empty = ()
        say(len_(empty))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "(1, 2, 3, 4)")
        self.assertEqual(lines[1], "0")

    def test_brack_indexing_positive_and_negative(self):
        code = """
        brack nums = (10, 20, 30, 40)
        say(nums[0])
        say(nums[2])
        say(nums[-1])
        say(nums[-2])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["10", "30", "40", "30"])

    def test_brack_immutability(self):
        code = """
        brack nums = (1, 2, 3)
        nums[1] = 99
        """
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("immutable", res.error["message"].lower())

    def test_brack_append_fails(self):
        code = """
        brack nums = (1, 2, 3)
        append_(nums, 4)
        """
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("mutable list", res.error["message"])

    def test_brack_conversion_listb_and_freeze(self):
        code = """
        brack nums = (1, 2, 3, 4)
        list b = listb_(nums)
        b[1] = 99
        say(b)
        say(nums)

        list original = [10, 20, 30]
        brack frozen = freeze_(original)
        original[0] = 999
        say(frozen)
        say(original)
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "[1, 99, 3, 4]")
        self.assertEqual(lines[1], "(1, 2, 3, 4)")
        self.assertEqual(lines[2], "(10, 20, 30)")
        self.assertEqual(lines[3], "[999, 20, 30]")

    def test_brack_iteration(self):
        code = """
        brack nums = (10, 20, 30)
        for i in nums {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["10", "20", "30"])

    def test_brack_ranged_iteration(self):
        code = """
        brack nums = (100, 200, 300, 400, 500)
        for i in nums(1; 3; 1) {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["200", "300", "400"])


class TestV2Dict(unittest.TestCase):
    def test_dict_creation_and_empty(self):
        code = """
        dict user = << "name": "raj", "age": 18, "skill": "python" >>
        say(user["name"])
        say(user["age"])
        say(len_(user))
        dict empty = << >>
        say(len_(empty))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["raj", "18", "3", "0"])

    def test_dict_valid_key_types(self):
        code = """
        dict d = << "str_key": 1, 42: 2, 3.14: 3, 'c': 4 >>
        say(d["str_key"], d[42], d[3.14], d['c'])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "1 2 3 4")

    def test_dict_reject_bool_key(self):
        res = execute("dict d = << true: \"bad\" >>")
        self.assertIsNotNone(res.error)
        self.assertIn("Boolean", res.error["message"])

        res2 = execute("dict d = << >>\nd[false] = \"bad\"")
        self.assertIsNotNone(res2.error)
        self.assertIn("Boolean", res2.error["message"])

    def test_dict_reject_collection_key(self):
        res = execute("dict d = << [1, 2]: \"bad\" >>")
        self.assertIsNotNone(res.error)
        self.assertIn("Collection", res.error["message"])

        res2 = execute("dict d = << (1, 2): \"bad\" >>")
        self.assertIsNotNone(res2.error)
        self.assertIn("Collection", res2.error["message"])

    def test_dict_reject_duplicate_key(self):
        code = """
        dict user = <<
            "name": "raj",
            "name": "something else"
        >>
        """
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("Duplicate", res.error["message"])

    def test_dict_mutation_and_new_key(self):
        code = """
        dict user = << "name": "raj" >>
        user["age"] = 18
        say(user["name"], user["age"])
        user["name"] = "rajditya"
        say(user["name"], user["age"])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "raj 18")
        self.assertEqual(lines[1], "rajditya 18")

    def test_dict_remove(self):
        code = """
        dict user = << "name": "raj", "age": 18 >>
        remove_(user, "age")
        say(len_(user))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "1")

        # Removing missing key raises error
        res2 = execute("dict user = << >>\nremove_(user, \"age\")")
        self.assertIsNotNone(res2.error)
        self.assertIn("KeyError", res2.error["message"])

    def test_dict_copy_semantics(self):
        code = """
        dict user = << 1: "raj", 2: "python" >>
        dict b = user
        b[1] = "changed"
        say(b[1])
        say(user[1])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["changed", "raj"])

    def test_dict_iteration_yields_key_value_bracks(self):
        code = """
        dict user = <<
            "name": "raj",
            "age": 18,
            "skill": "python"
        >>
        for i in user {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], '("name", "raj")')
        self.assertEqual(lines[1], '("age", 18)')
        self.assertEqual(lines[2], '("skill", "python")')

    def test_dict_keys_and_values_iteration(self):
        code = """
        dict user = << "name": "raj", "age": 18 >>
        for k in user.keys {
            say("key:", k)
        }
        for v in user.values {
            say("val:", v)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "key: name")
        self.assertEqual(lines[1], "key: age")
        self.assertEqual(lines[2], "val: raj")
        self.assertEqual(lines[3], "val: 18")

    def test_dict_ranged_iteration(self):
        code = """
        dict user = <<
            "name": "raj",
            "age": 18,
            "skill": "python",
            "city": "Mumbai",
            "country": "India"
        >>
        for i in user(1; 4; 2) {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], '("age", 18)')
        self.assertEqual(lines[1], '("city", "Mumbai")')

    def test_dict_ranged_keys_and_values(self):
        code = """
        dict user = << "a": 10, "b": 20, "c": 30, "d": 40 >>
        for k in user.keys(1; 2) {
            say(k)
        }
        for v in user.values(1; 2) {
            say(v)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["b", "c", "20", "30"])

    def test_dict_preserves_insertion_order(self):
        code = """
        dict user = << "a": 1, "b": 2, "c": 3 >>
        user["b"] = 200
        user["d"] = 4
        for k in user.keys {
            say(k)
        }
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip().split("\n"), ["a", "b", "c", "d"])


class TestV2CollectionInput(unittest.TestCase):
    def test_bk_integers(self):
        code = """
        brack nums = bk(input("enter"))
        say(nums)
        say(nums[0] + nums[1])
        """
        res = execute(code, input_handler=lambda p: "1,2,3,4")
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "(1, 2, 3, 4)")
        self.assertEqual(lines[1], "3")

    def test_bk_strings_with_quotes(self):
        code = """
        brack strings = bk(input("enter"))
        say(strings)
        say(strings[0])
        """
        res = execute(code, input_handler=lambda p: '"1","2","3"')
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], '("1", "2", "3")')
        self.assertEqual(lines[1], "1")

    def test_bk_mixed_quoted_and_unquoted(self):
        code = """
        brack data = bk(input("enter"))
        say(data)
        say(data[1] + data[3])
        """
        res = execute(code, input_handler=lambda p: '"raj",18,"python",20')
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], '("raj", 18, "python", 20)')
        self.assertEqual(lines[1], "38")

    def test_input_to_mutable_list(self):
        code = """
        list nums = listb_(bk(input("enter")))
        nums[1] = 99
        append_(nums, 500)
        say(nums)
        """
        res = execute(code, input_handler=lambda p: "1,2,3,4")
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "[1, 99, 3, 4, 500]")


class TestV2EdgeCases(unittest.TestCase):
    def test_nested_collection_types_preserved(self):
        code = """
        list a = [[1, 2], [3, 4]]
        brack b = ((1, 2), (3, 4))
        dict user = <<
            "skills": ["python", "c"],
            "numbers": (1, 2, 3),
            "profile": << "age": 18 >>
        >>
        say(a)
        say(b)
        say(user)
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "[[1, 2], [3, 4]]")
        self.assertEqual(lines[1], "((1, 2), (3, 4))")
        self.assertEqual(lines[2], '<< "skills": ["python", "c"], "numbers": (1, 2, 3), "profile": << "age": 18 >> >>')

    def test_invalid_range_arguments(self):
        # Step cannot be zero
        code = """
        list nums = [1, 2, 3]
        for i in nums(0; 2; 0) {
            say(i)
        }
        """
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("Range step cannot be zero", res.error["message"])

        # Non-integer range arg
        code2 = """
        list nums = [1, 2, 3]
        for i in nums(0; "bad") {
            say(i)
        }
        """
        res2 = execute(code2)
        self.assertIsNotNone(res2.error)
        self.assertIn("Range arguments must be integers", res2.error["message"])

    def test_single_element_brack(self):
        code = """
        brack single = (42,)
        say(single)
        say(single[0])
        say(len_(single))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "(42,)")
        self.assertEqual(lines[1], "42")
        self.assertEqual(lines[2], "1")

    def test_grouping_vs_brack(self):
        code = """
        int x = (10 + 20) * 2
        say(x)
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "60")

    def test_bk_whitespace_and_empty(self):
        code = """
        brack b1 = bk("")
        brack b2 = bk("   ")
        say(len_(b1), len_(b2))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "0 0")

    def test_bk_quoted_escapes(self):
        code = """
        brack b = bk(input())
        say(b[0])
        say(b[1])
        """
        res = execute(code, input_handler=lambda p: '"hello\\nworld", 100')
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "hello\nworld\n100")

    def test_type_errors_for_builtins(self):
        # len_ on integer
        res = execute("say(len_(42))")
        self.assertIsNotNone(res.error)
        self.assertIn("len_() not supported", res.error["message"])

        # listb_ on integer
        res2 = execute("listb_(42)")
        self.assertIsNotNone(res2.error)
        self.assertIn("listb_() expected", res2.error["message"])

        # freeze_ on integer
        res3 = execute("freeze_(42)")
        self.assertIsNotNone(res3.error)
        self.assertIn("freeze_() expected", res3.error["message"])


if __name__ == "__main__":
    unittest.main()

"""Tests for FlowLang V2 Standard Library (FlowLib).

Covers:
- import flowlib module loading and C-style direct scoping
- 13 Collection functions: min_, max_, sum_, asort_, dsort_, rev_, all_, any_, count_, index_, get_, pop_, clear_
- 11 String functions: lower_, upper_, capitalize_, title_, strip_, replace_, find_, startswith_, endswith_, split_, join_
- Error handling, mutability semantics, in-place behavior, and return values
"""

import unittest
from flowlang.engine import execute


class TestFlowLib(unittest.TestCase):
    def test_import_and_scope(self):
        # Without import, flowlib functions should be undefined
        res_no_import = execute("list nums = [1, 2]\nrev_(nums)")
        self.assertIsNotNone(res_no_import.error)
        self.assertIn("Undefined variable 'rev_'", res_no_import.error["message"])

        # With import flowlib, functions are accessible in global scope
        code = """
        import flowlib
        list nums = [1, 2, 3]
        rev_(nums)
        say(nums[0], nums[1], nums[2])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "3 2 1")

    def test_import_invalid_module(self):
        res = execute("import nonexistent_lib")
        self.assertIsNotNone(res.error)
        self.assertIn("Module 'nonexistent_lib' not found", res.error["message"])

    # ------------------ Collection Functions (13) ------------------

    def test_min_and_max(self):
        code = """
        import flowlib
        list nums = [10, -5, 42, 7]
        brack b = (3.5, 1.2, 9.9)
        say("min list:", min_(nums))
        say("max list:", max_(nums))
        say("min brack:", min_(b))
        say("max brack:", max_(b))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "min list: -5")
        self.assertEqual(lines[1], "max list: 42")
        self.assertEqual(lines[2], "min brack: 1.2")
        self.assertEqual(lines[3], "max brack: 9.9")

    def test_min_max_empty_error(self):
        res1 = execute("import flowlib\nlist empty = []\nmin_(empty)")
        self.assertIsNotNone(res1.error)
        self.assertIn("empty sequence", res1.error["message"])

        res2 = execute("import flowlib\nbrack empty = ()\nmax_(empty)")
        self.assertIsNotNone(res2.error)
        self.assertIn("empty sequence", res2.error["message"])

    def test_sum_total_and_range(self):
        code = """
        import flowlib
        list nums = [10, 20, 30, 40, 50]
        # Sum entire collection
        say("total:", sum_(nums))
        # Sum inclusive range [1, 3] -> 20 + 30 + 40 = 90
        say("range 1..3:", sum_(nums; 1; 3))
        # Negative index inclusive range [0, -2] -> 10 + 20 + 30 + 40 = 100
        say("range 0..-2:", sum_(nums; 0; -2))
        # Single element range
        say("range 2..2:", sum_(nums; 2; 2))
        # Brack summation with floats
        brack b = (1.5, 2.5, 3.0)
        say("brack sum:", sum_(b))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "total: 150")
        self.assertEqual(lines[1], "range 1..3: 90")
        self.assertEqual(lines[2], "range 0..-2: 100")
        self.assertEqual(lines[3], "range 2..2: 30")
        self.assertEqual(lines[4], "brack sum: 7.0")

    def test_asort_and_dsort(self):
        code = """
        import flowlib
        list nums = [40, 10, 50, 20, 30]
        # In-place ascending sort returns none
        lit ret1 = asort_(nums)
        say("asort return:", ret1)
        say("asorted:", nums[0], nums[1], nums[2], nums[3], nums[4])
        # In-place descending sort
        dsort_(nums)
        say("dsorted:", nums[0], nums[1], nums[2], nums[3], nums[4])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "asort return: none")
        self.assertEqual(lines[1], "asorted: 10 20 30 40 50")
        self.assertEqual(lines[2], "dsorted: 50 40 30 20 10")

    def test_asort_dsort_immutable_error(self):
        # Cannot sort immutable brack
        res = execute("import flowlib\nbrack b = (3, 1, 2)\nasort_(b)")
        self.assertIsNotNone(res.error)
        self.assertIn("requires a mutable list", res.error["message"])

    def test_rev_semantics(self):
        code = """
        import flowlib
        # List: mutates in-place, returns none
        list l = [1, 2, 3]
        lit ret = rev_(l)
        say("list rev ret:", ret)
        say("list after rev:", l[0], l[1], l[2])

        # Brack: leaves original intact, returns new reversed brack
        brack b = (10, 20, 30)
        brack rb = rev_(b)
        say("orig brack:", b[0], b[1], b[2])
        say("reversed brack:", rb[0], rb[1], rb[2])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "list rev ret: none")
        self.assertEqual(lines[1], "list after rev: 3 2 1")
        self.assertEqual(lines[2], "orig brack: 10 20 30")
        self.assertEqual(lines[3], "reversed brack: 30 20 10")

    def test_all_and_any(self):
        code = """
        import flowlib
        list all_true = [1, 2, "hello", true]
        list has_zero = [1, 0, 3]
        list all_falsy = [0, false, ""]
        say("all1:", all_(all_true))
        say("all2:", all_(has_zero))
        say("any1:", any_(has_zero))
        say("any2:", any_(all_falsy))
        say("empty all:", all_([]))
        say("empty any:", any_([]))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "all1: true")
        self.assertEqual(lines[1], "all2: false")
        self.assertEqual(lines[2], "any1: true")
        self.assertEqual(lines[3], "any2: false")
        self.assertEqual(lines[4], "empty all: true")
        self.assertEqual(lines[5], "empty any: false")

    def test_count_and_index(self):
        code = """
        import flowlib
        list items = [10, 20, 10, 30, 10]
        say("count 10:", count_(items; 10))
        say("count 99:", count_(items; 99))
        say("index 20:", index_(items; 20))
        say("index 99:", index_(items; 99))

        # String support
        str text = "banana"
        say("str count 'a':", count_(text; "a"))
        say("str index 'nan':", index_(text; "nan"))
        say("str index 'xyz':", index_(text; "xyz"))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "count 10: 3")
        self.assertEqual(lines[1], "count 99: 0")
        self.assertEqual(lines[2], "index 20: 1")
        self.assertEqual(lines[3], "index 99: -1")
        self.assertEqual(lines[4], "str count 'a': 3")
        self.assertEqual(lines[5], "str index 'nan': 2")
        self.assertEqual(lines[6], "str index 'xyz': -1")

    def test_get(self):
        code = """
        import flowlib
        dict d = << "name": "Flow", 1: 100 >>
        list l = [10, 20, 30]
        say("dict found:", get_(d; "name"))
        say("dict missing default:", get_(d; "missing"; "N/A"))
        say("dict missing none:", get_(d; "missing"))
        say("list found:", get_(l; 1))
        say("list neg index:", get_(l; -1))
        say("list out of bounds:", get_(l; 10; -1))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "dict found: Flow")
        self.assertEqual(lines[1], "dict missing default: N/A")
        self.assertEqual(lines[2], "dict missing none: none")
        self.assertEqual(lines[3], "list found: 20")
        self.assertEqual(lines[4], "list neg index: 30")
        self.assertEqual(lines[5], "list out of bounds: -1")

    def test_pop_and_clear(self):
        code = """
        import flowlib
        # List pop (in-place, returns none)
        list nums = [10, 20, 30, 40]
        lit ret1 = pop_(nums; 1)
        say("pop ret:", ret1)
        say("after pop idx 1:", nums[0], nums[1], nums[2])
        # Default pop removes last item (-1)
        pop_(nums)
        say("after pop last:", nums[0], nums[1])

        # Dict pop (in-place, returns none)
        dict user = << "name": "Raj", "role": "admin" >>
        pop_(user; "role")
        say("dict len after pop:", len_(user))
        say("user has name:", get_(user; "name"))
        say("user role gone:", get_(user; "role"; "missing"))

        # Clear
        clear_(nums)
        clear_(user)
        say("cleared list len:", len_(nums))
        say("cleared dict len:", len_(user))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "pop ret: none")
        self.assertEqual(lines[1], "after pop idx 1: 10 30 40")
        self.assertEqual(lines[2], "after pop last: 10 30")
        self.assertEqual(lines[3], "dict len after pop: 1")
        self.assertEqual(lines[4], "user has name: Raj")
        self.assertEqual(lines[5], "user role gone: missing")
        self.assertEqual(lines[6], "cleared list len: 0")
        self.assertEqual(lines[7], "cleared dict len: 0")

    def test_deletion_idiom_list(self):
        # Verify user's deletion idiom: index_(nums; val) -> pop_(nums; idx)
        code = """
        import flowlib
        list nums = [100, 200, 300, 400]
        int idx = index_(nums; 300)
        if idx != -1 {
            pop_(nums; idx)
        }
        say(nums[0], nums[1], nums[2])
        """
        res = execute(code)
        self.assertIsNone(res.error)
        self.assertEqual(res.output.strip(), "100 200 400")

    # ------------------ String Functions (11) ------------------

    def test_string_case_and_strip(self):
        code = """
        import flowlib
        str s = "  hElLo WoRlD  "
        say("lower:", lower_(s))
        say("upper:", upper_(s))
        say("capitalize:", capitalize_(strip_(s)))
        say("title:", title_(strip_(s)))
        say("strip:", strip_(s))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "lower:   hello world  ")
        self.assertEqual(lines[1], "upper:   HELLO WORLD  ")
        self.assertEqual(lines[2], "capitalize: Hello world")
        self.assertEqual(lines[3], "title: Hello World")
        self.assertEqual(lines[4], "strip: hElLo WoRlD")

    def test_replace_find_affixes(self):
        code = """
        import flowlib
        str s = "apple orange apple banana"
        say("replace:", replace_(s; "apple"; "pear"))
        say("find orange:", find_(s; "orange"))
        say("find grape:", find_(s; "grape"))
        say("starts apple:", startswith_(s; "apple"))
        say("starts orange:", startswith_(s; "orange"))
        say("ends banana:", endswith_(s; "banana"))
        say("ends pear:", endswith_(s; "pear"))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "replace: pear orange pear banana")
        self.assertEqual(lines[1], "find orange: 6")
        self.assertEqual(lines[2], "find grape: -1")
        self.assertEqual(lines[3], "starts apple: true")
        self.assertEqual(lines[4], "starts orange: false")
        self.assertEqual(lines[5], "ends banana: true")
        self.assertEqual(lines[6], "ends pear: false")

    def test_split_and_join(self):
        code = """
        import flowlib
        str s = "alpha,beta,gamma"
        list parts = split_(s; ",")
        say("split len:", len_(parts))
        say("part 0:", parts[0])
        say("part 1:", parts[1])
        say("part 2:", parts[2])

        str rejoined = join_(parts; " -> ")
        say("rejoined:", rejoined)

        # Split on whitespace default
        str sentence = "one  two   three"
        list words = split_(sentence)
        say("words count:", len_(words))
        say("words joined:", join_(words; "|"))
        """
        res = execute(code)
        self.assertIsNone(res.error)
        lines = res.output.strip().split("\n")
        self.assertEqual(lines[0], "split len: 3")
        self.assertEqual(lines[1], "part 0: alpha")
        self.assertEqual(lines[2], "part 1: beta")
        self.assertEqual(lines[3], "part 2: gamma")
        self.assertEqual(lines[4], "rejoined: alpha -> beta -> gamma")
        self.assertEqual(lines[5], "words count: 3")
        self.assertEqual(lines[6], "words joined: one|two|three")

    def test_pop_clear_immutable_error(self):
        res1 = execute("import flowlib\nbrack b = (1, 2, 3)\npop_(b)")
        self.assertIsNotNone(res1.error)
        self.assertIn("requires a mutable list or dict", res1.error["message"])

        res2 = execute("import flowlib\nbrack b = (1, 2, 3)\nclear_(b)")
        self.assertIsNotNone(res2.error)
        self.assertIn("requires a mutable list or dict", res2.error["message"])

    def test_str_functions_type_error(self):
        res = execute("import flowlib\nlower_(123)")
        self.assertIsNotNone(res.error)
        self.assertIn("expected str", res.error["message"])


if __name__ == "__main__":
    unittest.main()


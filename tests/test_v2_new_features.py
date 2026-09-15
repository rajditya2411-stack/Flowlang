import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestV2NewFeatures(unittest.TestCase):
    def run_code(self, source: str):
        res = execute(source)
        if res.error:
            self.fail(f"Execution failed with error: {res.error['message']}\nFormatted:\n{res.formatted_error}")
        return res.output.splitlines()

    def test_immutability_by_default(self):
        code = '''
        int x = 10
        x = 20
        '''
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("immutable", res.error["message"].lower())

    def test_mut_modifier(self):
        code = '''
        mut int x = 10
        x = 20
        say(x)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["20"])

    def test_mut_type_safety(self):
        code = '''
        mut int x = 10
        x = "hello"
        '''
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])

    def test_mut_lit_dynamism(self):
        code = '''
        mut lit y = 10
        y = "hello"
        say(y)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["hello"])

    def test_immutable_lit(self):
        code = '''
        lit y = 10
        y = 20
        '''
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("immutable", res.error["message"].lower())

    def test_list_shared_reference_by_default(self):
        code = '''
        list a = [1, 2, 3]
        list b = a
        b[0] = 99
        say(a[0])
        say(b[0])
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["99", "99"])

    def test_list_clone_property(self):
        code = '''
        list a = [1, 2, 3]
        list c = a.clone
        c[0] = 99
        say(a[0])
        say(c[0])
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["1", "99"])

    def test_list_no_mut_required(self):
        code = '''
        list a = [1, 2]
        a = [3, 4]
        say(a[0])
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["3"])

    def test_compound_assignment_identifier(self):
        code = '''
        mut int x = 10
        x += 5
        x -= 3
        x *= 2
        x //= 4
        x %= 5
        say(x)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["1"])

    def test_compound_assignment_index(self):
        code = '''
        list a = [10, 20]
        a[0] += 5
        a[1] //= 2
        say(a[0])
        say(a[1])
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["15", "10"])

    def test_break_continue_while(self):
        code = '''
        mut int i = 0
        mut int sum = 0
        while i < 10 {
            i += 1
            if i == 3 {
                continue
            }
            if i == 6 {
                break
            }
            sum += i
        }
        say(sum)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["12"])

    def test_break_continue_for(self):
        code = '''
        mut int sum = 0
        for i in (0; i < 10; i = i + 1) {
            if i == 2 {
                continue
            }
            if i == 5 {
                break
            }
            sum += i
        }
        say(sum)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["8"])

    def test_core_min_max(self):
        code = '''
        say(min(10, 20))
        say(max(10, 20))
        say(min(5.5, 2.2))
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["10", "20", "2.2"])

    def test_flowlib_abs_clamp(self):
        code = '''
        import flowlib
        say(abs_(-42))
        say(clamp_(15, 0, 10))
        say(clamp_(-5, 0, 10))
        say(clamp_(7, 0, 10))
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["42", "10", "0", "7"])

    def test_struct_definition_and_access(self):
        code = '''
        struct Person = << str name, int age >>
        Person p = << "Raj", 20 >>
        say(p.name)
        say(p.age)
        '''
        res = self.run_code(code)
        self.assertEqual(res, ["Raj", "20"])

    def test_struct_type_mismatch(self):
        code = '''
        struct Person = << str name, int age >>
        Person p = << "Raj", "invalid_age" >>
        '''
        res = execute(code)
        self.assertIsNotNone(res.error)
        self.assertIn("Type mismatch", res.error["message"])


if __name__ == '__main__':
    unittest.main()

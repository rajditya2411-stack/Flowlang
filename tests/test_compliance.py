"""Unittest integration for FlowLang Compliance Test Suite.

Discovers and runs all .flow fixtures under tests/compliance/ to ensure
they are run during standard `python -m unittest discover tests`.
"""

import unittest
from pathlib import Path
from tests.compliance_runner import run_fixture


class TestComplianceSuite(unittest.TestCase):
    """Dynamic test runner for compliance fixtures."""
    pass


def _generate_test_method(flow_path: Path):
    def test_method(self):
        result = run_fixture(flow_path)
        if not result.passed:
            if result.error_message:
                self.fail(f"{flow_path.name}: {result.error_message}")
            else:
                self.assertEqual(
                    result.expected,
                    result.actual,
                    f"\nCompliance mismatch in {flow_path}:\nExpected:\n{result.expected}\n\nActual:\n{result.actual}"
                )
    return test_method


# Dynamically register each fixture as a test case method
compliance_dir = Path(__file__).parent / "compliance"
for flow_file in sorted(compliance_dir.rglob("*.flow")):
    rel_name = flow_file.relative_to(compliance_dir).as_posix().replace("/", "_").replace(".flow", "")
    test_name = f"test_compliance_{rel_name}"
    setattr(TestComplianceSuite, test_name, _generate_test_method(flow_file))


if __name__ == "__main__":
    unittest.main()

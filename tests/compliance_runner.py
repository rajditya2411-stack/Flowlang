"""FlowLang Language-Agnostic Compliance Test Runner.

Executes all .flow programs in tests/compliance/ through FlowLang's public
engine execution boundary and compares observable output against .expected files.
"""

import os
import sys
import difflib
from pathlib import Path
from typing import NamedTuple, Optional

# Ensure src is in sys.path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from flowlang.engine import execute


class TestResult(NamedTuple):
    file_path: Path
    passed: bool
    expected: str
    actual: str
    error_message: Optional[str] = None


def run_fixture(flow_path: Path) -> TestResult:
    """Execute a single .flow fixture and compare with its .expected counterpart."""
    expected_path = flow_path.with_suffix(".expected")
    if not expected_path.is_file():
        return TestResult(
            file_path=flow_path,
            passed=False,
            expected="",
            actual="",
            error_message=f"Missing expected file: {expected_path}",
        )

    with open(flow_path, "r", encoding="utf-8-sig") as f:
        source_code = f.read()

    with open(expected_path, "r", encoding="utf-8-sig") as f:
        expected_output = f.read().replace("\r\n", "\n").strip()

    # Execute through FlowLang's public engine boundary
    result = execute(source_code)

    # Capture observable output (standard output + formatted error if present)
    parts = []
    if result.output:
        parts.append(result.output)
    if result.formatted_error:
        parts.append(result.formatted_error)
    elif result.value is not None and not result.output:
        parts.append(str(result.value))

    actual_output = "\n".join(parts).replace("\r\n", "\n").strip()

    passed = (actual_output == expected_output)
    return TestResult(
        file_path=flow_path,
        passed=passed,
        expected=expected_output,
        actual=actual_output,
    )


def discover_and_run(compliance_dir: Optional[Path] = None, verbose: bool = True) -> int:
    """Discover all .flow fixtures under compliance_dir and report results."""
    if compliance_dir is None:
        compliance_dir = Path(__file__).parent / "compliance"

    flow_files = sorted(compliance_dir.rglob("*.flow"))
    if not flow_files:
        print(f"No .flow fixtures found in {compliance_dir}")
        return 1

    total = len(flow_files)
    passed_count = 0
    failed_count = 0

    print("=" * 70)
    print(f"FLOWLANG COMPLIANCE TEST SUITE ({total} fixtures)")
    print(f"Directory: {compliance_dir}")
    print("=" * 70)

    for flow_path in flow_files:
        rel_path = flow_path.relative_to(compliance_dir.parent)
        res = run_fixture(flow_path)

        if res.passed:
            passed_count += 1
            if verbose:
                print(f"  [PASS] {rel_path}")
        else:
            failed_count += 1
            print(f"  [FAIL] {rel_path}")
            if res.error_message:
                print(f"         {res.error_message}")
            else:
                diff = difflib.unified_diff(
                    res.expected.splitlines(keepends=True),
                    res.actual.splitlines(keepends=True),
                    fromfile=f"expected ({flow_path.name})",
                    tofile=f"actual ({flow_path.name})",
                    lineterm="",
                )
                print("         Diff:")
                for line in diff:
                    print(f"           {line.rstrip()}")

    print("-" * 70)
    print(f"Results: {passed_count}/{total} passed, {failed_count} failed")
    print("=" * 70)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(discover_and_run())

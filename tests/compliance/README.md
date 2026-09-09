# FlowLang Compliance Test Suite

This directory contains the language-agnostic compliance test suite for FlowLang.

---

## 1. What is the Compliance Suite?

The compliance suite is a collection of `.flow` source programs paired with `.expected` output files. It verifies that any FlowLang engine implementation (the current Python reference interpreter or a future C/C++ core) correctly evaluates FlowLang programs and produces exact observable output.

```
.flow source fixture ──► FlowLang Engine ──► Observable Output ──► Compare against .expected
```

---

## 2. Why are `.flow` Fixtures Used?

Unlike traditional unit tests that import host language classes (`Lexer`, `Parser`, `Interpreter`), compliance fixtures are pure FlowLang source files:

1. **Portability:** Fixtures test the language specification rather than internal class structures.
2. **Reusability:** When the FlowLang core is rewritten in C/C++ or compiled to WebAssembly, this exact same test suite can run against the new binary without rewriting test logic.
3. **Black-Box Verification:** The suite checks user-observable behavior (standard output, return values, formatted error diagnostics).

---

## 3. Directory Structure

```
tests/compliance/
├── arithmetic/       # Integer/float arithmetic, precedence, comparisons, logical ops
├── variables/        # Variable assignment, re-assignment, augmented assignments
├── strings/          # String literals, escape sequences, concatenation
├── conditionals/     # if, elif, else, nested branches
├── loops/            # while, for..in range(), for..in string
├── builtins/         # print(), say(), len(), abs(), type(), type casts
└── errors/           # Syntax and runtime error diagnostics
```

---

## 4. How to Run the Compliance Suite

### Standalone Runner (Direct execution)
```bash
python tests/compliance_runner.py
```

### Standard Unittest Discovery (Runs both unit tests and compliance fixtures)
```bash
python -m unittest discover tests -v
```

---

## 5. How to Add a New Compliance Test

1. Pick or create the appropriate subdirectory under `tests/compliance/<category>/`.
2. Create a `<test_name>.flow` file with valid or erroneous FlowLang code.
3. Create a `<test_name>.expected` file containing the exact expected observable output (or error diagnostic).
4. Run `python tests/compliance_runner.py` to verify that your new test passes.

---

## 6. Why Independence from Python Matters

FlowLang is designed to evolve into a compiled systems language. Keeping the compliance suite strictly independent of Python ensures:
- Zero coupling to Python's object model or exception mechanics.
- A single, immutable source of truth for language behavior across all present and future implementations.

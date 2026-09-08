# FlowLang — Language Core

FlowLang is a clean, hand-crafted interpreted programming language built from scratch in Python with zero external compiler dependencies.

FlowLang features **Python-style syntax** (colons `:`, indentation-based blocks, direct assignments, `True`/`False`/`None`, `and`/`or`/`not`, `#` comments, and `print`).

The language engine follows an explicit multi-stage architecture:
```
FlowLang source code
        ↓
     Lexer (Indentation, Tokens & source locations)
        ↓
     Parser (Recursive-descent with Suites & Precedence)
        ↓
       AST (Pure structural data nodes)
        ↓
   Interpreter (Tree-walk evaluator)
        ↓
      Runtime (Lexical scopes & builtins)
        ↓
   Output / Structured Errors
```

---

## Project Structure

```
flowlang/
├── src/
│   └── flowlang/
│       ├── __init__.py      # Package metadata & version
│       ├── tokens.py        # Token types (INDENT, DEDENT, etc.) and Token class
│       ├── lexer.py         # Lexical analyzer with Python indentation tracking
│       ├── ast.py           # Abstract Syntax Tree node definitions
│       ├── parser.py        # Recursive-descent parser with suites & operator precedence
│       ├── runtime.py       # Scopes (Environment), builtins (print/say), stringifier
│       ├── interpreter.py   # Tree-walk AST evaluator (short-circuit logic, math, control flow)
│       ├── errors.py        # Structured error types with line/column pointers
│       └── engine.py        # Clean pipeline facade (for CLI, REPL, & Playground API)
│
├── tests/
│   ├── test_lexer.py        # Lexer tests (indentation, tokens, escapes, malformed input)
│   ├── test_parser.py       # Parser & AST tests (suites, precedence, grouping, expressions)
│   ├── test_interpreter.py  # Evaluation tests (arithmetic, variables, if/elif/else, while)
│   ├── test_errors.py       # Error formatting and source pointer tests
│   └── test_engine.py       # End-to-end pipeline execution tests
│
├── examples/
│   ├── hello.flow           # Hello World example
│   ├── arithmetic.flow      # Arithmetic precedence and conditionals
│   └── error_example.flow   # Example showing formatted error output
│
├── main.py                  # CLI & REPL entry point
├── requirements.txt         # Project requirements (Standard Library)
└── README.md
```

---

## Quick Start

### 1. Run an Example File
```bash
python main.py run examples/hello.flow
```

Output:
```
Hello, world from FlowLang
```

```bash
python main.py run examples/arithmetic.flow
```

Output:
```
Result is: 55
Result is greater than 50!
```

### 2. Interactive REPL
Launch the FlowLang REPL:
```bash
python main.py repl
```

Example session:
```
FlowLang REPL (v0.1.0)
Type 'exit' or press Ctrl+C to exit.

flow> a = 4
flow> b = 4
flow> a + b
8
flow> if a == b:
...       print("Equal!")
Equal!
flow> exit
Goodbye!
```

---

## Error Handling

FlowLang does not expose raw Python stack traces. Errors include line numbers, column positions, and visual caret pointers:

```
FlowLang RuntimeError: Undefined variable 'invalid_var'
  at line 4, column 7

  4 | print(invalid_var)
            ^
```

---

## Running Tests

All 43 tests run using Python's built-in `unittest`:

```bash
python -m unittest discover tests -v
```

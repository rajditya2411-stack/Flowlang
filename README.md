# FlowLang (fl) — V1 Specification & Implementation

FlowLang is a clean, hand-crafted programming language situated between Python and C/C++, built from scratch with zero external compiler dependencies.

FlowLang V1 combines the readability of modern scripting languages with brace-based scoping `{}` and hybrid variable semantics: dynamically typed variables (`lit`) alongside strictly typed variables (`int`, `flt`, `str`, `char`, `bool`).

---

## Language Pipeline Architecture

```
FlowLang source code (.flow)
            ↓
     Lexer (Tokens, comments, source locations)
            ↓
    Parser (Recursive-descent, C precedence, AST generation)
            ↓
       AST (Pure structural data nodes)
            ↓
   Interpreter (Tree-walk evaluator)
            ↓
     Runtime (Lexical scopes, typed variables, builtins)
            ↓
     Output (say) / Structured Errors with Source Pointers
```

---

## Language Specifications (V1)

### 1. Keywords & Lexical Structure
- All keywords are strictly **lowercase**:
  `int`, `flt`, `str`, `char`, `bool`, `lit`, `if`, `elif`, `else`, `while`, `do`, `for`, `in`, `dfn`, `return`, `say`, `and`, `or`, `not`, `true`, `false`.
- **Block scoping**: Code blocks use curly braces `{}`. Statements do not require semicolons.
- **Comments**:
  - Single-line: `# comment`
  - Multi-line: `/* comment */`

### 2. Variables & Typing
FlowLang supports two declaration paradigms:

- **Dynamic variables (`lit`)**:
  ```flow
  lit x = 10
  x = "now a string"    # Reassignment to any type is allowed
  ```

- **Static typed variables (`int`, `flt`, `str`, `char`, `bool`)**:
  ```flow
  int count = 10
  flt rate = 3.14
  str name = "Raj"
  char grade = 'A'
  bool is_active = true

  # Reassignments must match the declared type; mismatch raises a RuntimeError:
  # count = "hello"  -> RuntimeError: Type mismatch
  ```

- **Literals**:
  - Strings: Double quotes `"..."` (e.g. `"Hello"`)
  - Characters: Single quotes `'...'` (e.g. `'c'`)
  - Booleans: `true` and `false`

### 3. Input & Output
- **Output**: `say(...)` prints values separated by spaces with a newline. (`print` is removed in V1).
  ```flow
  say("Hello,", name)
  ```
- **Input**:
  - String input: `str x = input("Enter name: ")` or `str x = input()`
  - Typed input conversion:
    ```flow
    int age = int(input("Enter age: "))
    flt score = flt(input("Enter score: "))
    char ch = char(input("Enter initial: "))
    bool flag = bool(input("Enter status: "))
    ```

### 4. Control Flow & Loops

- **Conditionals (`if`, `elif`, `else`)**:
  ```flow
  int score = 85
  if score >= 90 {
      say("Grade: A")
  } elif score >= 80 {
      say("Grade: B")
  } else {
      say("Grade: C")
  }
  ```

- **For Loops**:
  C-style 3-clause loop header inside `(...)`. The loop variable is automatically declared in the loop scope:
  ```flow
  for i in (0; i < 5; i = i + 1) {
      say("Step:", i)
  }
  ```

- **While Loops**:
  ```flow
  int i = 5
  while i > 0 {
      say("Countdown:", i)
      i = i - 1
  }
  ```

- **Do-While Loops**:
  ```flow
  int n = 0
  do {
      say("Value:", n)
      n = n + 1
  } while n < 3
  ```

### 5. Functions
Functions are declared using `dfn` with curly braces `{}` and `return`:
```flow
dfn add(int a, int b) {
    return a + b
}

int total = add(5, 10)
say("Total is:", total)
```

### 6. Operators & Precedence
- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
  - Division `/` always returns float (`flt`), e.g., `20 / 4` evaluates to `5.0`.
  - Power: Built-in `pow_(base, exp)`.
- **String Operations**:
  - Multiplication: `"raj" * 2` evaluates to `"rajraj"`, `"raj" * 0` evaluates to `""`. (Multiplier must be a non-negative integer).
  - Concatenation: `"raj" + 2` evaluates to `"raj2"`, `"raj" + "kumar"` evaluates to `"rajkumar"`.
- **Precedence Hierarchy**: Strict C operator precedence with left-to-right associativity:
  1. Primary: Literals, variables, grouping `()`
  2. Unary: `-`, `not`
  3. Multiplicative: `*`, `/`, `%`
  4. Additive: `+`, `-`
  5. Relational: `<`, `<=`, `>`, `>=`
  6. Equality: `==`, `!=`
  7. Logical AND: `and`
  8. Logical OR: `or`

---

## Quick Start

### 1. Run a FlowLang Program
```bash
python main.py run examples/hello.flow
# Or shorthand:
python main.py examples/hello.flow
```

### 2. Interactive REPL
```bash
python main.py repl
```

### 3. Launch Web Playground
```bash
python main.py playground
```
Opens the browser-based editor and visual console at **`http://localhost:8000`**.

---

## Running Tests

### Full Test Suite (116 unit & integration tests)
```bash
python -m unittest discover tests -v
```

### Language-Agnostic Compliance Suite (25 fixtures)
```bash
python tests/compliance_runner.py
```

---

## Roadmap (Future V2 Scope)
The following features are intentionally reserved for future versions:
- Array / list literals `[...]` and indexing
- Bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`)
- Explicit `nil` / `null` keyword
- C/C++ compiler backend

# FlowLang — Language Core & Playground

FlowLang is a clean, hand-crafted interpreted programming language built from scratch in Python with zero external compiler dependencies.

FlowLang features **Python-style syntax** (colons `:`, indentation-based blocks, direct assignments, augmented assignments `+=`/`-=`/`*=`, `if`/`elif`/`else`, `while`, `for ... in ...`, `range`, `print`, `True`/`False`/`None`, `and`/`or`/`not`, and `#` comments).

---

## Language Core Architecture
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
      Runtime (Lexical scopes, range, builtins)
        ↓
   Output / Structured Errors
```

---

## Language Features (Current Scope)

### 1. Variables & Assignments
```python
a = 4
b = 4
print("a + b =", a + b)  # 8

# Augmented assignments
a += 10
b -= 2
```

### 2. Loops

**While Loops:**
```python
i = 5
while i > 0:
    print("Countdown:", i)
    i -= 1
```

**For Loops with `range()`:**
```python
# Counting up
for i in range(5):
    print("Step:", i)

# Counting down
for count in range(5, 0, -1):
    print(count)

# Iterating over text
for letter in "FlowLang":
    print(letter)
```

### 3. Conditionals (`if`, `elif`, `else`)
```python
score = 85
if score >= 90:
    print("Grade: A")
elif score >= 80:
    print("Grade: B")
else:
    print("Grade: C")
```

### 4. Built-in Functions
- `print(*args)` / `say(*args)`
- `range(stop)` / `range(start, stop)` / `range(start, stop, step)`
- `len(obj)`
- `abs(x)`
- `type(x)`
- `int(x)`, `float(x)`, `str(x)`, `bool(x)`

---

## Quick Start

### 1. Launch Browser Playground
```bash
python main.py playground
```
Opens the interactive web UI at **`http://localhost:8500`**.

### 2. Run a FlowLang File
```bash
python main.py run examples/for_loop.flow
```

### 3. Interactive REPL
```bash
python main.py repl
```

---

## Running Tests

Run all 56 tests using Python's built-in `unittest`:
```bash
python -m unittest discover tests -v
```

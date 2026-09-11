/**
 * FlowLang Playground Client Application
 * Handles code editing, line numbering, auto-indentation, and execution API calls.
 */

const EXAMPLES = {
  calculator: `# Calculator & Variables
int a = 4
int b = 4
say("a =", a)
say("b =", b)
say("a + b =", a + b)`,

  hello: `# Hello World & Strings
str greeting = "Hello, world from"
str language = "FlowLang"
say(greeting, language)`,

  arithmetic: `# Arithmetic Precedence & Conditionals
int a = 10
int b = 20
flt result = (a + b) * 2 - 10 / 2
say("Result is:", result)

if result > 50 {
    say("Result is greater than 50!")
} else {
    say("Result is 50 or less.")
}`,

  conditionals: `# If / Elif / Else Statements
int score = 85
str grade = ""

if score >= 90 {
    grade = "A"
} elif score >= 80 {
    grade = "B"
} elif score >= 70 {
    grade = "C"
} else {
    grade = "F"
}

say("Score:", score, "-> Grade:", grade)`,

  loops: `# Loops: for, while, do-while
say("--- For Loop ---")
for i in (0; i < 4; i = i + 1) {
    say("i =", i)
}

say("--- While Loop ---")
int w = 3
while w > 0 {
    say("w =", w)
    w = w - 1
}

say("--- Do-While Loop ---")
int d = 0
do {
    say("d =", d)
    d = d + 1
} while d < 2`,

  functions: `# Functions (dfn / return)
dfn add(int x, int y) {
    return x + y
}

dfn greet(str name) {
    say("Hello,", name)
}

greet("FlowLang User")
say("3 + 7 =", add(3, 7))`,

  logic: `# Logical Operators (and / or / not)
int x = 10
int y = 20

bool is_valid = x > 0 and y < 50
say("Is valid?", is_valid)

bool is_special = not (x == 10) or y == 20
say("Is special?", is_special)`,

  error_demo: `# Visual Error Pointer Demo
str username = "Raj"
say("Hello", username)
say(missing_var)`,

  collections: `# Collections: list, brack, dict
list nums = [10, 20, 30]
append_(nums, 40)
say("List:", nums)

brack b = (1, 2, 3)
say("Brack:", b)

dict user = << "name": "Raj", "age": 18 >>
user["skill"] = "FlowLang"
say("User name:", user["name"])

say("--- Dict Iteration ---")
for item in user {
    say(item)
}`
};

// DOM Elements
const editor = document.getElementById("code-editor");
const lineNumbers = document.getElementById("line-numbers");
const outputConsole = document.getElementById("console-output");
const runBtn = document.getElementById("run-btn");
const clearBtn = document.getElementById("clear-btn");
const exampleSelect = document.getElementById("example-select");
const execStatus = document.getElementById("exec-status");
const cursorPos = document.getElementById("cursor-pos");

// Initialize Editor with default example or saved draft
function init() {
  const saved = localStorage.getItem("flowlang_code");
  if (saved) {
    editor.value = saved;
  } else {
    editor.value = EXAMPLES.calculator;
  }
  updateLineNumbers();
  updateCursorPosition();
}

// Update line numbers gutter
function updateLineNumbers() {
  const lines = editor.value.split("\n");
  const count = lines.length;
  let lineStr = "";
  for (let i = 1; i <= count; i++) {
    lineStr += (i === 1 ? "" : "\n") + i;
  }
  lineNumbers.textContent = lineStr;
  lineNumbers.scrollTop = editor.scrollTop;
}

// Sync line number scrolling with textarea
editor.addEventListener("scroll", () => {
  lineNumbers.scrollTop = editor.scrollTop;
});

// Update cursor position in status bar
function updateCursorPosition() {
  const text = editor.value.substring(0, editor.selectionStart);
  const lines = text.split("\n");
  const currentLine = lines.length;
  const currentCol = lines[lines.length - 1].length + 1;
  cursorPos.textContent = `Line ${currentLine}, Col ${currentCol}`;
}

editor.addEventListener("keyup", () => {
  updateCursorPosition();
  updateLineNumbers();
});

editor.addEventListener("click", updateCursorPosition);

// Input handling (save to localStorage, update lines)
editor.addEventListener("input", () => {
  updateLineNumbers();
  localStorage.setItem("flowlang_code", editor.value);
});

// Handle Tab & Auto-indentation on Enter
editor.addEventListener("keydown", (e) => {
  // Shortcut: Ctrl+Enter or Cmd+Enter to Run
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    runCode();
    return;
  }

  // Tab key: Insert 4 spaces
  if (e.key === "Tab") {
    e.preventDefault();
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const tabSpaces = "    ";
    editor.value = editor.value.substring(0, start) + tabSpaces + editor.value.substring(end);
    editor.selectionStart = editor.selectionEnd = start + 4;
    updateLineNumbers();
    return;
  }

  // Enter key: Maintain indentation or add 4 spaces after colon ':'
  if (e.key === "Enter") {
    const start = editor.selectionStart;
    const textBefore = editor.value.substring(0, start);
    const lines = textBefore.split("\n");
    const currentLine = lines[lines.length - 1];

    const match = currentLine.match(/^(\s*)/);
    let indent = match ? match[1] : "";

    if (currentLine.trim().endsWith(":")) {
      indent += "    ";
    }

    if (indent.length > 0) {
      e.preventDefault();
      const insertText = "\n" + indent;
      editor.value = editor.value.substring(0, start) + insertText + editor.value.substring(editor.selectionEnd);
      editor.selectionStart = editor.selectionEnd = start + insertText.length;
      updateLineNumbers();
    }
  }
});

// Example Selector Change
exampleSelect.addEventListener("change", (e) => {
  const key = e.target.value;
  if (EXAMPLES[key]) {
    editor.value = EXAMPLES[key];
    updateLineNumbers();
    localStorage.setItem("flowlang_code", editor.value);
    runCode();
  }
});

// Clear Button
clearBtn.addEventListener("click", () => {
  editor.value = "";
  updateLineNumbers();
  outputConsole.className = "console-output empty-state";
  outputConsole.innerHTML = "Editor cleared. Type your FlowLang code and click <strong>Run</strong>.";
  execStatus.className = "status-badge status-ready";
  execStatus.textContent = "Ready";
  localStorage.removeItem("flowlang_code");
});

// Run Button
runBtn.addEventListener("click", runCode);

// Execute Code via /api/run
async function runCode() {
  const code = editor.value;
  if (!code.trim()) {
    outputConsole.className = "console-output empty-state";
    outputConsole.innerHTML = "Nothing to run. Write some code first!";
    return;
  }

  const inputs = [];
  const inputMatches = code.match(/input\s*\(\s*(?:"([^"]*)"|'([^']*)')?\s*\)/g);
  if (inputMatches) {
    for (const match of inputMatches) {
      const promptMatch = match.match(/input\s*\(\s*(?:"([^"]*)"|'([^']*)')?\s*\)/);
      const promptText = (promptMatch && (promptMatch[1] || promptMatch[2])) || "Enter input:";
      const val = window.prompt(promptText, "5");
      if (val !== null) {
        inputs.push(val);
      }
    }
  }

  execStatus.className = "status-badge status-ready";
  execStatus.textContent = "Running...";
  const startTime = performance.now();

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, inputs })
    });

    const elapsed = Math.round(performance.now() - startTime);
    const data = await response.json();

    outputConsole.className = "console-output";
    outputConsole.innerHTML = "";

    if (data.error) {
      execStatus.className = "status-badge status-error";
      execStatus.textContent = `Error (${elapsed}ms)`;

      const errorDiv = document.createElement("div");
      errorDiv.className = "output-error";
      errorDiv.textContent = data.formatted_error || `Error: ${data.error.message}`;
      outputConsole.appendChild(errorDiv);

      if (data.output) {
        const outDiv = document.createElement("div");
        outDiv.className = "output-text";
        outDiv.style.marginTop = "12px";
        outDiv.textContent = data.output;
        outputConsole.appendChild(outDiv);
      }
    } else {
      execStatus.className = "status-badge status-success";
      execStatus.textContent = `Executed (${elapsed}ms)`;

      if (data.output) {
        const outDiv = document.createElement("div");
        outDiv.className = "output-text";
        outDiv.textContent = data.output;
        outputConsole.appendChild(outDiv);
      }

      if (data.value !== null && data.value !== undefined) {
        const valDiv = document.createElement("div");
        valDiv.className = "output-value";
        valDiv.textContent = `➜ Result: ${data.value}`;
        outputConsole.appendChild(valDiv);
      }

      if (!data.output && (data.value === null || data.value === undefined)) {
        outputConsole.innerHTML = '<span style="color: #8b949e;">(Program completed with no output)</span>';
      }
    }
  } catch (err) {
    execStatus.className = "status-badge status-error";
    execStatus.textContent = "Server Error";
    outputConsole.className = "console-output";
    outputConsole.innerHTML = `<div class="output-error">Failed to connect to FlowLang backend server: ${err.message}</div>`;
  }
}

// Run on initial load
init();

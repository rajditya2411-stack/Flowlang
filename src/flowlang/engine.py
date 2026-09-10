"""FlowLang Engine Pipeline.

Provides the unified interface to the FlowLang pipeline:
Source Code -> Lexer -> Tokens -> Parser -> AST -> Interpreter -> Runtime -> Result.
Decoupled for use by CLI, REPL, tests, and future Playground API.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional
from flowlang.lexer import Lexer
from flowlang.parser import Parser
from flowlang.interpreter import Interpreter
from flowlang.runtime import Environment, stringify_value
from flowlang.errors import FlowLangError


@dataclass
class ExecutionResult:
    """Result of running FlowLang source code."""
    output: str
    error: Optional[dict[str, Any]] = None
    value: Any = None
    formatted_error: Optional[str] = None


def execute(
    source_code: str,
    environment: Optional[Environment] = None,
    input_handler: Optional[Callable[[str], str]] = None,
) -> ExecutionResult:
    """Execute FlowLang source code and return a structured ExecutionResult."""
    output_lines: list[str] = []

    def capture_output(text: str) -> None:
        output_lines.append(text)

    try:
        # 1. Lexical Analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        # 2. Syntactic Analysis / Parsing
        parser = Parser(tokens, source_code=source_code)
        program = parser.parse()

        # 3. Interpretation / Execution
        interpreter = Interpreter(
            globals_env=environment,
            output_handler=capture_output,
            input_handler=input_handler,
            source_code=source_code,
        )
        result_value = interpreter.interpret(program)

        return ExecutionResult(
            output="\n".join(output_lines),
            error=None,
            value=result_value,
            formatted_error=None,
        )

    except FlowLangError as err:
        return ExecutionResult(
            output="\n".join(output_lines),
            error={
                "message": err.message,
                "line": err.line,
                "column": err.column,
                "type": err.error_name,
            },
            value=None,
            formatted_error=err.format_error(source_code),
        )

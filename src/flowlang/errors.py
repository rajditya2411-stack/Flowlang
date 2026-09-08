"""FlowLang Error System.

Provides structured, readable errors with line, column, and source code context.
No raw Python stack traces are exposed to FlowLang users.
"""

from typing import Optional


class FlowLangError(Exception):
    """Base class for all FlowLang errors."""

    def __init__(
        self,
        message: str,
        line: int = 1,
        column: int = 1,
        source_code: Optional[str] = None,
        error_name: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.source_code = source_code
        self.error_name = error_name or self.__class__.__name__

    def format_error(self, source_code: Optional[str] = None) -> str:
        """Format the error into a clean, human-readable message with source context."""
        code = source_code or self.source_code
        header = f"FlowLang {self.error_name}: {self.message}"
        location = f"  at line {self.line}, column {self.column}"

        if code:
            lines = code.splitlines()
            if 1 <= self.line <= len(lines):
                source_line = lines[self.line - 1]
                prefix = f"  {self.line} | "
                pointer_indent = " " * (len(prefix) + max(0, self.column - 1))
                pointer = pointer_indent + "^"
                return f"{header}\n{location}\n\n{prefix}{source_line}\n{pointer}"

        return f"{header}\n{location}"

    def __str__(self) -> str:
        return self.format_error()


class LexerError(FlowLangError):
    """Raised during tokenization / lexical analysis."""

    def __init__(self, message: str, line: int = 1, column: int = 1, source_code: Optional[str] = None):
        super().__init__(message, line, column, source_code, error_name="LexerError")


class ParserError(FlowLangError):
    """Raised during parsing / syntactic analysis."""

    def __init__(self, message: str, line: int = 1, column: int = 1, source_code: Optional[str] = None):
        super().__init__(message, line, column, source_code, error_name="ParserError")


class FlowRuntimeError(FlowLangError):
    """Raised during AST evaluation / runtime execution."""

    def __init__(self, message: str, line: int = 1, column: int = 1, source_code: Optional[str] = None):
        super().__init__(message, line, column, source_code, error_name="RuntimeError")

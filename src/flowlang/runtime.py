"""FlowLang Runtime and Environment.

Manages lexical scopes, variable binding, built-in functions, and execution state.
Completely decoupled from UI and OS-specific input/output.
"""

from typing import Any, Callable, Optional
from flowlang.errors import FlowRuntimeError


class FlowCallable:
    """Base class for callable objects (built-in functions, user-defined functions)."""

    def arity(self) -> Optional[int]:
        """Expected number of arguments, or None if variadic."""
        return None

    def call(self, interpreter: Any, arguments: list[Any], line: int, column: int) -> Any:
        raise NotImplementedError


class BuiltinFunction(FlowCallable):
    """Wrapper for built-in functions implemented in the host language."""

    def __init__(self, name: str, fn: Callable[..., Any], expected_arity: Optional[int] = None):
        self.name = name
        self._fn = fn
        self._arity = expected_arity

    def arity(self) -> Optional[int]:
        return self._arity

    def call(self, interpreter: Any, arguments: list[Any], line: int, column: int) -> Any:
        if self._arity is not None and len(arguments) != self._arity:
            raise FlowRuntimeError(
                f"Function '{self.name}' expected {self._arity} arguments, but got {len(arguments)}",
                line=line,
                column=column,
                source_code=interpreter.source_code,
            )
        return self._fn(interpreter, arguments, line, column)

    def __repr__(self) -> str:
        return f"<builtin fn {self.name}>"


class Environment:
    """Lexical scope environment supporting nested parent scopes."""

    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        """Define a new variable in the current local scope."""
        self.values[name] = value

    def get(self, name: str, line: int, column: int, source_code: Optional[str] = None) -> Any:
        """Retrieve variable value from current or enclosing scopes."""
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name, line, column, source_code)

        raise FlowRuntimeError(
            f"Undefined variable '{name}'",
            line=line,
            column=column,
            source_code=source_code,
        )

    def assign(self, name: str, value: Any, line: int, column: int, source_code: Optional[str] = None) -> None:
        """Assign to an already existing variable in current or enclosing scopes."""
        if name in self.values:
            self.values[name] = value
            return

        if self.parent is not None:
            self.parent.assign(name, value, line, column, source_code)
            return

        raise FlowRuntimeError(
            f"Cannot assign to undefined variable '{name}'",
            line=line,
            column=column,
            source_code=source_code,
        )


def stringify_value(value: Any) -> str:
    """Format a FlowLang runtime value into its canonical string representation."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        # Clean formatting: 5.0 -> 5.0, but avoid long IEEE 754 precision artifacts if simple
        text = str(value)
        if text.endswith(".0"):
            return text
        return text
    return str(value)

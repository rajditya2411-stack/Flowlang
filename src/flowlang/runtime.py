"""FlowLang Runtime and Environment.

Manages lexical scopes, variable binding with static/dynamic type checking,
callable objects, and canonical value representation.
"""

from typing import Any, Callable, Optional
from flowlang.errors import FlowRuntimeError


class Char:
    """Represents a FlowLang character value ('c')."""

    def __init__(self, value: str):
        if len(value) != 1:
            raise ValueError("Char must be exactly one character")
        self.value = value

    def __repr__(self) -> str:
        return f"'{self.value}'"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Char):
            return self.value == other.value
        if isinstance(other, str) and len(other) == 1:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class ReturnSignal(Exception):
    """Raised by return statements to unwind execution back to the caller."""

    def __init__(self, value: Any = None):
        self.value = value
        super().__init__()


def get_type_name(value: Any) -> str:
    """Returns FlowLang type name for a runtime value."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "flt"
    if isinstance(value, Char):
        return "char"
    if isinstance(value, str):
        return "str"
    if isinstance(value, FlowCallable):
        return "function"
    return type(value).__name__


def check_type_match(expected_type: Optional[str], value: Any) -> bool:
    """Checks whether value conforms to expected_type ('lit' or None matches any)."""
    if expected_type is None or expected_type == "lit":
        return True
    if expected_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "flt":
        return isinstance(value, float) and not isinstance(value, bool)
    if expected_type == "str":
        return isinstance(value, str)
    if expected_type == "char":
        return isinstance(value, Char) or (isinstance(value, str) and len(value) == 1)
    if expected_type == "bool":
        return isinstance(value, bool)
    return True


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


class UserFunction(FlowCallable):
    """User-defined FlowLang function declared via dfn."""

    def __init__(self, name: str, parameters: list[str], body: Any, closure: "Environment"):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.closure = closure

    def arity(self) -> Optional[int]:
        return len(self.parameters)

    def call(self, interpreter: Any, arguments: list[Any], line: int, column: int) -> Any:
        if len(arguments) != len(self.parameters):
            raise FlowRuntimeError(
                f"Function '{self.name}' expects {len(self.parameters)} argument(s), got {len(arguments)}",
                line=line,
                column=column,
                source_code=interpreter.source_code,
            )

        call_env = Environment(parent=self.closure)
        for param_name, arg_val in zip(self.parameters, arguments):
            call_env.define(param_name, arg_val, type_name="lit")

        previous_env = interpreter.environment
        try:
            interpreter.environment = call_env
            interpreter.execute_block(self.body.statements, call_env)
        except ReturnSignal as ret:
            return ret.value
        finally:
            interpreter.environment = previous_env

        return None

    def __repr__(self) -> str:
        return f"<function {self.name}>"


class Environment:
    """Lexical scope environment supporting nested parent scopes and type tracking."""

    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.types: dict[str, Optional[str]] = {}

    def define(
        self,
        name: str,
        value: Any,
        type_name: Optional[str] = "lit",
        line: int = 1,
        column: int = 1,
        source_code: Optional[str] = None,
    ) -> None:
        """Define a new variable in current local scope with its type constraint."""
        if not check_type_match(type_name, value):
            raise FlowRuntimeError(
                f"Type mismatch: cannot initialize variable '{name}' of type '{type_name}' with value of type '{get_type_name(value)}'",
                line=line,
                column=column,
                source_code=source_code,
            )
        self.values[name] = value
        self.types[name] = type_name

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
        """Assign to an existing variable in current or enclosing scope, enforcing type safety."""
        if name in self.values:
            expected_type = self.types.get(name, "lit")
            if not check_type_match(expected_type, value):
                raise FlowRuntimeError(
                    f"Type mismatch: cannot assign value of type '{get_type_name(value)}' to variable '{name}' declared as '{expected_type}'",
                    line=line,
                    column=column,
                    source_code=source_code,
                )
            self.values[name] = value
            return

        if self.parent is not None and self.parent._exists(name):
            self.parent.assign(name, value, line, column, source_code)
            return

        raise FlowRuntimeError(
            f"Undefined variable '{name}' (must be declared before assignment)",
            line=line,
            column=column,
            source_code=source_code,
        )

    def _exists(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent._exists(name)
        return False


def stringify_value(value: Any) -> str:
    """Format a FlowLang runtime value into its canonical string representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        text = str(value)
        return text
    if isinstance(value, Char):
        return value.value
    if value is None:
        return ""
    return str(value)

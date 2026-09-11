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


class Brack(tuple):
    """Represents a FlowLang immutable ordered collection (brack)."""

    def __repr__(self) -> str:
        return stringify_element(self)

    def __str__(self) -> str:
        return stringify_element(self)


class FlowDict(dict):
    """Represents a FlowLang mutable ordered key-value collection."""

    def __repr__(self) -> str:
        return stringify_element(self)

    def __str__(self) -> str:
        return stringify_element(self)


class DictKeysView:
    """Ordered keys view of a FlowLang dictionary."""

    def __init__(self, dictionary: Any):
        self.dictionary = dictionary

    def __iter__(self):
        return iter(list(self.dictionary.keys()))

    def __len__(self):
        return len(self.dictionary)

    def __getitem__(self, idx: int):
        return list(self.dictionary.keys())[idx]

    def __repr__(self):
        return f"<dict_keys {list(self.dictionary.keys())}>"


class DictValuesView:
    """Ordered values view of a FlowLang dictionary."""

    def __init__(self, dictionary: Any):
        self.dictionary = dictionary

    def __iter__(self):
        return iter(list(self.dictionary.values()))

    def __len__(self):
        return len(self.dictionary)

    def __getitem__(self, idx: int):
        return list(self.dictionary.values())[idx]

    def __repr__(self):
        return f"<dict_values {list(self.dictionary.values())}>"


def parse_bk_input(raw: Any, line: int = 1, col: int = 1, source_code: Optional[str] = None) -> Brack:
    """Safe FlowLang collection input parser without using eval().
    
    Parses comma-separated elements:
    - Quoted values (\"...\") are strictly strings, even if they look like numbers.
    - Unquoted numeric values are integers (or floats if containing a dot).
    - Unquoted true/false are booleans.
    - Single-quoted values ('c') are characters.
    """
    if not isinstance(raw, str):
        raw = stringify_value(raw)
    raw = raw.strip()
    if not raw:
        return Brack(())

    items: list[Any] = []
    i = 0
    n = len(raw)

    while i < n:
        while i < n and raw[i] in " \t\r\n":
            i += 1
        if i >= n:
            break

        # Double-quoted string
        if raw[i] == '"':
            start = i
            i += 1
            s_val = ""
            closed = False
            while i < n:
                if raw[i] == '\\' and i + 1 < n:
                    escape_char = raw[i + 1]
                    if escape_char == '"': s_val += '"'
                    elif escape_char == 'n': s_val += '\n'
                    elif escape_char == 't': s_val += '\t'
                    elif escape_char == '\\': s_val += '\\'
                    else: s_val += escape_char
                    i += 2
                elif raw[i] == '"':
                    i += 1
                    closed = True
                    break
                else:
                    s_val += raw[i]
                    i += 1
            if not closed:
                raise FlowRuntimeError(f"Unterminated string in collection input: {raw[start:]}", line=line, column=col, source_code=source_code)
            items.append(s_val)

        # Single-quoted character
        elif raw[i] == "'":
            start = i
            i += 1
            c_val = ""
            closed = False
            while i < n:
                if raw[i] == '\\' and i + 1 < n:
                    c_val += raw[i + 1]
                    i += 2
                elif raw[i] == "'":
                    i += 1
                    closed = True
                    break
                else:
                    c_val += raw[i]
                    i += 1
            if not closed:
                raise FlowRuntimeError(f"Unterminated character in collection input: {raw[start:]}", line=line, column=col, source_code=source_code)
            items.append(Char(c_val) if len(c_val) == 1 else c_val)

        else:
            # Unquoted token up to comma
            start = i
            while i < n and raw[i] != ',':
                i += 1
            token_str = raw[start:i].strip()
            if token_str:
                if token_str == "true":
                    items.append(True)
                elif token_str == "false":
                    items.append(False)
                else:
                    try:
                        items.append(int(token_str))
                    except ValueError:
                        try:
                            items.append(float(token_str))
                        except ValueError:
                            items.append(token_str)

        while i < n and raw[i] in " \t\r\n":
            i += 1
        if i < n and raw[i] == ',':
            i += 1

    return Brack(items)


def validate_dict_key(key: Any, line: int = 1, column: int = 1, source_code: Optional[str] = None) -> None:
    """Validates that a key is permitted in a FlowLang dictionary."""
    if isinstance(key, bool):
        raise FlowRuntimeError(
            "Boolean keys are not allowed in dictionaries",
            line=line,
            column=column,
            source_code=source_code,
        )
    if isinstance(key, (list, Brack, tuple, dict, FlowDict)):
        raise FlowRuntimeError(
            f"Collection of type '{get_type_name(key)}' cannot be used as a dictionary key",
            line=line,
            column=column,
            source_code=source_code,
        )
    if not isinstance(key, (str, int, float, Char)):
        raise FlowRuntimeError(
            f"Invalid dictionary key type '{get_type_name(key)}'",
            line=line,
            column=column,
            source_code=source_code,
        )


def make_independent_copy(val: Any) -> Any:
    """Recursively creates an independent copy of mutable collections (list, dict)."""
    if isinstance(val, list):
        return [make_independent_copy(item) for item in val]
    if isinstance(val, (FlowDict, dict)):
        return FlowDict({k: make_independent_copy(v) for k, v in val.items()})
    return val


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
    if isinstance(value, list):
        return "list"
    if isinstance(value, (Brack, tuple)):
        return "brack"
    if isinstance(value, (FlowDict, dict)):
        return "dict"
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
    if expected_type == "list":
        return isinstance(value, list)
    if expected_type == "brack":
        return isinstance(value, (Brack, tuple))
    if expected_type == "dict":
        return isinstance(value, (FlowDict, dict))
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
        self.values[name] = make_independent_copy(value)
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
            self.values[name] = make_independent_copy(value)
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


def stringify_element(value: Any) -> str:
    """Format an element when displayed nested inside collections."""
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, Char):
        return f"'{value.value}'"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(stringify_element(x) for x in value) + "]"
    if isinstance(value, (Brack, tuple)):
        if not value:
            return "()"
        if len(value) == 1:
            return f"({stringify_element(value[0])},)"
        return "(" + ", ".join(stringify_element(x) for x in value) + ")"
    if isinstance(value, (FlowDict, dict)):
        if not value:
            return "<< >>"
        items = ", ".join(f"{stringify_element(k)}: {stringify_element(v)}" for k, v in value.items())
        return f"<< {items} >>"
    return stringify_value(value)


def stringify_value(value: Any) -> str:
    """Format a FlowLang runtime value into its canonical string representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return str(value)
    if isinstance(value, Char):
        return value.value
    if isinstance(value, list):
        return "[" + ", ".join(stringify_element(x) for x in value) + "]"
    if isinstance(value, (Brack, tuple)):
        if not value:
            return "()"
        if len(value) == 1:
            return f"({stringify_element(value[0])},)"
        return "(" + ", ".join(stringify_element(x) for x in value) + ")"
    if isinstance(value, (FlowDict, dict)):
        if not value:
            return "<< >>"
        items = ", ".join(f"{stringify_element(k)}: {stringify_element(v)}" for k, v in value.items())
        return f"<< {items} >>"
    if value is None:
        return "none"
    return str(value)

"""FlowLang Runtime and Environment.

Manages lexical scopes, variable binding with static/dynamic type checking,
callable objects, and canonical value representation.
"""

from typing import Any, Callable, Optional
from dataclasses import dataclass
from flowlang.errors import FlowRuntimeError


class Char:
    """Represents a FlowLang character value ('c')."""

    def __init__(self, value: str):
        if len(value) != 1:
            raise ValueError("Char must be exactly one character")
        if value.isdigit():
            raise ValueError("Numeric characters '0'-'9' are invalid in Char in FlowLang V2")
        self.value = value

    def __repr__(self) -> str:
        return f"'{self.value}'"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Char):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class ReturnSignal(Exception):
    """Raised by return statements to unwind execution back to the caller."""

    def __init__(self, value: Any = None):
        self.value = value
        super().__init__()


class UserRaiseSignal(Exception):
    """Raised by raise statements to unwind execution until caught by try/catch."""

    def __init__(self, message: str, line: int = 1, column: int = 1):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(message)


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


@dataclass
class StructType:
    name: str
    fields: list[tuple[str, str]]  # list of (field_name, type_name)


class StructInstance:
    def __init__(self, struct_type: StructType, fields: dict[str, Any]):
        self.struct_type = struct_type
        self.fields = fields

    def __repr__(self) -> str:
        f_strs = ", ".join(f"{k}: {stringify_element(v)}" for k, v in self.fields.items())
        return f"<< {f_strs} >>"


@dataclass
class EnumType:
    name: str
    members: list[str]  # list of member names in declaration order


class EnumValue:
    def __init__(self, enum_type: EnumType, member: str, index: int):
        self.enum_type = enum_type
        self.member = member
        self.index = index

    def __repr__(self) -> str:
        return f"{self.enum_type.name}.{self.member}"

    def __str__(self) -> str:
        return f"{self.enum_type.name}.{self.member}"

    def __hash__(self) -> int:
        return hash((self.enum_type.name, self.member))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, EnumValue):
            return self.enum_type.name == other.enum_type.name and self.member == other.member
        return False


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
    """Recursively creates an independent copy of mutable collections (list, dict, StructInstance)."""
    if isinstance(val, list):
        return [make_independent_copy(item) for item in val]
    if isinstance(val, (FlowDict, dict)):
        return FlowDict({k: make_independent_copy(v) for k, v in val.items()})
    if isinstance(val, StructInstance):
        return StructInstance(val.struct_type, {k: make_independent_copy(v) for k, v in val.fields.items()})
    return val


def deep_freeze(val: Any) -> Any:
    """Recursively converts nested lists into immutable Bracks."""
    if isinstance(val, (list, Brack, tuple)):
        return Brack(deep_freeze(item) for item in val)
    if isinstance(val, (FlowDict, dict)):
        return FlowDict({k: deep_freeze(v) for k, v in val.items()})
    return val


def get_type_name(value: Any) -> str:
    """Returns FlowLang type name for a runtime value."""
    if value is None:
        return "none"
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
    if isinstance(value, StructInstance):
        return value.struct_type.name
    if isinstance(value, EnumValue):
        return value.enum_type.name
    if isinstance(value, FlowCallable):
        return "function"
    return type(value).__name__


def check_type_match(expected_type: Optional[str], value: Any) -> bool:
    """Checks whether value conforms to expected_type ('lit' matches any except mutable list)."""
    if expected_type is None:
        return True
    if expected_type == "lit":
        return not isinstance(value, list)
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
    if expected_type == "function":
        return isinstance(value, FlowCallable)
    if isinstance(value, StructInstance):
        return value.struct_type.name == expected_type
    if isinstance(value, EnumValue):
        return value.enum_type.name == expected_type
    standard_types = {"lit", "int", "flt", "str", "char", "bool", "list", "brack", "dict", "function"}
    if expected_type not in standard_types:
        return False
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

    def __init__(
        self,
        name: str,
        parameters: list[tuple[str, str]],
        return_type: str,
        body: Any,
        closure: "Environment",
    ):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
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

        current_depth = getattr(interpreter, "call_depth", 0)
        if current_depth >= 1000:
            raise FlowRuntimeError(
                "Maximum recursion depth exceeded (1000)",
                line=line,
                column=column,
                source_code=interpreter.source_code,
            )
        interpreter.call_depth = current_depth + 1

        call_env = Environment(parent=self.closure, is_function=True)
        for (param_name, param_type), arg_val in zip(self.parameters, arguments):
            if param_type == "lit":
                if isinstance(arg_val, list):
                    raise FlowRuntimeError(
                        f"Argument '{param_name}' declared as 'lit' cannot accept a mutable list (use freeze_() to pass as immutable brack)",
                        line=line,
                        column=column,
                        source_code=interpreter.source_code,
                    )
            else:
                if not check_type_match(param_type, arg_val):
                    raise FlowRuntimeError(
                        f"Type mismatch for argument '{param_name}': expected '{param_type}', got '{get_type_name(arg_val)}'",
                        line=line,
                        column=column,
                        source_code=interpreter.source_code,
                    )
            call_env.define(param_name, arg_val, type_name=param_type, line=line, column=column, source_code=interpreter.source_code)

        previous_env = interpreter.environment
        has_returned = False
        ret_val = None
        try:
            interpreter.environment = call_env
            interpreter.execute_block(self.body.statements, call_env)
        except ReturnSignal as ret:
            has_returned = True
            ret_val = ret.value
        finally:
            interpreter.environment = previous_env
            interpreter.call_depth = current_depth

        # Enforce return type
        if not has_returned or ret_val is None:
            if self.return_type != "lit":
                raise FlowRuntimeError(
                    f"Function '{self.name}' declared return type '{self.return_type}', but produced 'none' (missing return statement)",
                    line=line,
                    column=column,
                    source_code=interpreter.source_code,
                )
            return None

        if self.return_type == "lit":
            if isinstance(ret_val, list):
                raise FlowRuntimeError(
                    f"Function '{self.name}' declared return type 'lit' cannot return a mutable list (use freeze_() to return immutable brack)",
                    line=line,
                    column=column,
                    source_code=interpreter.source_code,
                )
            return ret_val

        if not check_type_match(self.return_type, ret_val):
            raise FlowRuntimeError(
                f"Return type mismatch: function '{self.name}' declared return type '{self.return_type}', but returned value of type '{get_type_name(ret_val)}'",
                line=line,
                column=column,
                source_code=interpreter.source_code,
            )

        return ret_val

    def __repr__(self) -> str:
        return f"<function {self.name}>"


class Environment:
    """Lexical scope environment supporting nested parent scopes, type tracking, mutability, structs, and enums."""

    def __init__(self, parent: Optional["Environment"] = None, is_function: bool = False):
        self.parent = parent
        self.is_function = is_function
        self.values: dict[str, Any] = {}
        self.types: dict[str, Optional[str]] = {}
        self.is_mutable: dict[str, bool] = {}
        self.struct_types: dict[str, StructType] = {}
        self.enum_types: dict[str, EnumType] = {}
        self.declared_globals: set[str] = set()

    def get_enclosing_function_env(self) -> Optional["Environment"]:
        env = self
        while env is not None:
            if env.is_function:
                return env
            env = env.parent
        return None

    def _exists_in_function_hierarchy(self, name: str, fn_env: "Environment") -> bool:
        env = self
        while env is not None:
            if name in env.values:
                return True
            if env is fn_env:
                break
            env = env.parent
        return False

    def declare_global(self, name: str) -> None:
        self.declared_globals.add(name)

    def define_struct(self, name: str, struct_type: StructType, line: int = 1, column: int = 1, source_code: Optional[str] = None) -> None:
        if name in self.values or name in self.struct_types or name in self.enum_types:
            raise FlowRuntimeError(
                f"Identifier '{name}' is already defined in this scope",
                line=line,
                column=column,
                source_code=source_code,
            )
        self.struct_types[name] = struct_type

    def get_struct(self, name: str) -> Optional[StructType]:
        if name in self.struct_types:
            return self.struct_types[name]
        if self.parent is not None:
            return self.parent.get_struct(name)
        return None

    def define_enum(self, name: str, enum_type: EnumType, line: int = 1, column: int = 1, source_code: Optional[str] = None) -> None:
        if name in self.values or name in self.struct_types or name in self.enum_types:
            raise FlowRuntimeError(
                f"Identifier '{name}' is already defined in this scope",
                line=line,
                column=column,
                source_code=source_code,
            )
        self.enum_types[name] = enum_type

    def get_enum(self, name: str) -> Optional[EnumType]:
        if name in self.enum_types:
            return self.enum_types[name]
        if self.parent is not None:
            return self.parent.get_enum(name)
        return None

    def define(
        self,
        name: str,
        value: Any,
        type_name: Optional[str] = "lit",
        is_mutable: bool = False,
        line: int = 1,
        column: int = 1,
        source_code: Optional[str] = None,
    ) -> None:
        """Define a new variable in current local scope with its type constraint and mutability."""
        if name in self.values or name in self.struct_types or name in self.enum_types:
            if not isinstance(self.values.get(name), BuiltinFunction):
                raise FlowRuntimeError(
                    f"Identifier '{name}' is already defined in this scope",
                    line=line,
                    column=column,
                    source_code=source_code,
                )
        if not check_type_match(type_name, value):
            raise FlowRuntimeError(
                f"Type mismatch: cannot initialize variable '{name}' of type '{type_name}' with value of type '{get_type_name(value)}'",
                line=line,
                column=column,
                source_code=source_code,
            )
        # Lists have shared reference semantics by default
        if isinstance(value, list):
            self.values[name] = value
        else:
            self.values[name] = make_independent_copy(value)
        self.types[name] = type_name
        self.is_mutable[name] = is_mutable

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
        """Assign to an existing variable in current or enclosing scope, enforcing mutability and type safety."""
        if name == "none":
            raise FlowRuntimeError(
                "Cannot assign to reserved value 'none'",
                line=line,
                column=column,
                source_code=source_code,
            )
        if name in self.values:
            expected_type = self.types.get(name, "lit")
            if expected_type != "list" and not self.is_mutable.get(name, False):
                raise FlowRuntimeError(
                    f"Cannot reassign immutable variable '{name}' (declare with 'mut' to allow reassignment)",
                    line=line,
                    column=column,
                    source_code=source_code,
                )
            if not check_type_match(expected_type, value):
                raise FlowRuntimeError(
                    f"Type mismatch: cannot assign value of type '{get_type_name(value)}' to variable '{name}' declared as '{expected_type}'",
                    line=line,
                    column=column,
                    source_code=source_code,
                )
            if isinstance(value, list):
                self.values[name] = value
            else:
                self.values[name] = make_independent_copy(value)
            return

        # Check if we are inside a function assigning to an outer variable
        fn_env = self.get_enclosing_function_env()
        if fn_env is not None and not self._exists_in_function_hierarchy(name, fn_env):
            if fn_env.parent is not None and fn_env.parent._exists(name):
                if name not in fn_env.declared_globals:
                    raise FlowRuntimeError(
                        f"Cannot assign to global variable '{name}' without 'global' declaration in function",
                        line=line,
                        column=column,
                        source_code=source_code,
                    )

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

    def get_type(self, name: str) -> Optional[str]:
        if name in self.types:
            return self.types[name]
        if self.parent is not None:
            return self.parent.get_type(name)
        return None

    def get_mutability(self, name: str) -> bool:
        if name in self.is_mutable:
            return self.is_mutable[name]
        if self.parent is not None:
            return self.parent.get_mutability(name)
        return False


def stringify_element(value: Any) -> str:
    """Format an element when displayed nested inside collections."""
    if value is None:
        return "none"
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
    if isinstance(value, StructInstance):
        items = ", ".join(f"{k}: {stringify_element(v)}" for k, v in value.fields.items())
        return f"<< {items} >>"
    if isinstance(value, EnumValue):
        return f"{value.enum_type.name}.{value.member}"
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
    if isinstance(value, StructInstance):
        items = ", ".join(f"{k}: {stringify_element(v)}" for k, v in value.fields.items())
        return f"<< {items} >>"
    if isinstance(value, EnumValue):
        return f"{value.enum_type.name}.{value.member}"
    if value is None:
        return "none"
    return str(value)

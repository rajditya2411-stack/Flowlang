"""FlowLang Standard Library: FlowLib.

Provides 24 advanced collection and string manipulation functions:
- Collection Functions: min_, max_, sum_, asort_, dsort_, rev_, all_, any_, count_, index_, get_, pop_, clear_
- String Functions: lower_, upper_, capitalize_, title_, strip_, replace_, find_, startswith_, endswith_, split_, join_
"""

from typing import Any
from flowlang.runtime import (
    Brack,
    FlowDict,
    Char,
    BuiltinFunction,
    get_type_name,
    stringify_value,
)
from flowlang.errors import FlowRuntimeError


def _check_col(val: Any, fn_name: str, line: int, col: int, source_code: Any) -> None:
    if not isinstance(val, (list, Brack, tuple)):
        raise FlowRuntimeError(
            f"{fn_name}() expected list or brack, got '{get_type_name(val)}'",
            line=line,
            column=col,
            source_code=source_code,
        )


def _check_str(val: Any, fn_name: str, line: int, col: int, source_code: Any) -> None:
    if not isinstance(val, str):
        raise FlowRuntimeError(
            f"{fn_name}() expected str, got '{get_type_name(val)}'",
            line=line,
            column=col,
            source_code=source_code,
        )


def _to_str(val: Any) -> str:
    if isinstance(val, Char):
        return val.value
    if isinstance(val, str):
        return val
    return stringify_value(val)


# ------------------ Collection Functions (13) ------------------

def fn_min(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
    if len(args) != 1:
        raise FlowRuntimeError(f"min_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "min_", line, col, interpreter.source_code)
    if len(collection) == 0:
        raise FlowRuntimeError("min_() arg is an empty sequence", line=line, column=col, source_code=interpreter.source_code)
    try:
        return min(collection)
    except TypeError as e:
        raise FlowRuntimeError(f"min_() comparison error: {e}", line=line, column=col, source_code=interpreter.source_code)


def fn_max(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
    if len(args) != 1:
        raise FlowRuntimeError(f"max_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "max_", line, col, interpreter.source_code)
    if len(collection) == 0:
        raise FlowRuntimeError("max_() arg is an empty sequence", line=line, column=col, source_code=interpreter.source_code)
    try:
        return max(collection)
    except TypeError as e:
        raise FlowRuntimeError(f"max_() comparison error: {e}", line=line, column=col, source_code=interpreter.source_code)


def fn_sum(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
    if len(args) not in (1, 2, 3):
        raise FlowRuntimeError(f"sum_() expected 1, 2, or 3 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "sum_", line, col, interpreter.source_code)

    start = 0
    end = len(collection) - 1

    if len(args) >= 2:
        s_val = args[1]
        if not isinstance(s_val, int) or isinstance(s_val, bool):
            raise FlowRuntimeError("sum_() start index must be an integer", line=line, column=col, source_code=interpreter.source_code)
        start = s_val
    if len(args) == 3:
        e_val = args[2]
        if not isinstance(e_val, int) or isinstance(e_val, bool):
            raise FlowRuntimeError("sum_() end index must be an integer", line=line, column=col, source_code=interpreter.source_code)
        end = e_val

    # Handle negative indices
    if start < 0:
        start = len(collection) + start
    if end < 0:
        end = len(collection) + end

    if start < 0 or start > len(collection) or end < -1 or end >= len(collection):
        raise FlowRuntimeError(f"sum_() index range [{start}, {end}] out of bounds for length {len(collection)}", line=line, column=col, source_code=interpreter.source_code)

    if start > end:
        return 0

    sub = collection[start : end + 1]
    has_float = False
    total = 0

    for item in sub:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise FlowRuntimeError(f"sum_() requires numeric elements, got '{get_type_name(item)}'", line=line, column=col, source_code=interpreter.source_code)
        if isinstance(item, float):
            has_float = True
        total += item

    return float(total) if has_float else int(total)


def fn_asort(interpreter: Any, args: list[Any], line: int, col: int) -> None:
    if len(args) != 1:
        raise FlowRuntimeError(f"asort_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    lst = args[0]
    if not isinstance(lst, list):
        raise FlowRuntimeError(f"asort_() requires a mutable list, got '{get_type_name(lst)}'", line=line, column=col, source_code=interpreter.source_code)
    try:
        lst.sort()
    except TypeError as e:
        raise FlowRuntimeError(f"asort_() sort error: {e}", line=line, column=col, source_code=interpreter.source_code)
    return None


def fn_dsort(interpreter: Any, args: list[Any], line: int, col: int) -> None:
    if len(args) != 1:
        raise FlowRuntimeError(f"dsort_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    lst = args[0]
    if not isinstance(lst, list):
        raise FlowRuntimeError(f"dsort_() requires a mutable list, got '{get_type_name(lst)}'", line=line, column=col, source_code=interpreter.source_code)
    try:
        lst.sort(reverse=True)
    except TypeError as e:
        raise FlowRuntimeError(f"dsort_() sort error: {e}", line=line, column=col, source_code=interpreter.source_code)
    return None


def fn_rev(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
    if len(args) != 1:
        raise FlowRuntimeError(f"rev_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    val = args[0]
    if isinstance(val, list):
        val.reverse()
        return None
    elif isinstance(val, (Brack, tuple)):
        return Brack(reversed(val))
    else:
        raise FlowRuntimeError(f"rev_() requires a list or brack, got '{get_type_name(val)}'", line=line, column=col, source_code=interpreter.source_code)


def fn_all(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
    if len(args) != 1:
        raise FlowRuntimeError(f"all_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "all_", line, col, interpreter.source_code)
    return all(interpreter._is_truthy(x) for x in collection)


def fn_any(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
    if len(args) != 1:
        raise FlowRuntimeError(f"any_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "any_", line, col, interpreter.source_code)
    return any(interpreter._is_truthy(x) for x in collection)


def fn_count(interpreter: Any, args: list[Any], line: int, col: int) -> int:
    if len(args) != 2:
        raise FlowRuntimeError(f"count_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection, item = args[0], args[1]
    if isinstance(collection, str):
        target = _to_str(item)
        return collection.count(target)
    if isinstance(collection, (list, Brack, tuple)):
        return collection.count(item)
    raise FlowRuntimeError(f"count_() requires a list, brack, or str, got '{get_type_name(collection)}'", line=line, column=col, source_code=interpreter.source_code)


def fn_index(interpreter: Any, args: list[Any], line: int, col: int) -> int:
    if len(args) != 2:
        raise FlowRuntimeError(f"index_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection, item = args[0], args[1]
    if isinstance(collection, str):
        target = _to_str(item)
        return collection.find(target)
    if isinstance(collection, (list, Brack, tuple)):
        try:
            return collection.index(item)
        except ValueError:
            return -1
    raise FlowRuntimeError(f"index_() requires a list, brack, or str, got '{get_type_name(collection)}'", line=line, column=col, source_code=interpreter.source_code)


def fn_get(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
    if len(args) not in (2, 3):
        raise FlowRuntimeError(f"get_() expected 2 or 3 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    key_or_idx = args[1]
    default = args[2] if len(args) == 3 else None

    if isinstance(collection, (FlowDict, dict)):
        return collection.get(key_or_idx, default)

    if isinstance(collection, (list, Brack, tuple)):
        if not isinstance(key_or_idx, int) or isinstance(key_or_idx, bool):
            raise FlowRuntimeError(f"get_() list/brack index must be an integer, got '{get_type_name(key_or_idx)}'", line=line, column=col, source_code=interpreter.source_code)
        idx = len(collection) + key_or_idx if key_or_idx < 0 else key_or_idx
        if 0 <= idx < len(collection):
            return collection[idx]
        return default

    raise FlowRuntimeError(f"get_() requires a dict, list, or brack, got '{get_type_name(collection)}'", line=line, column=col, source_code=interpreter.source_code)


def fn_pop(interpreter: Any, args: list[Any], line: int, col: int) -> None:
    if len(args) not in (1, 2):
        raise FlowRuntimeError(f"pop_() expected 1 or 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]

    if isinstance(collection, list):
        idx = args[1] if len(args) == 2 else -1
        if not isinstance(idx, int) or isinstance(idx, bool):
            raise FlowRuntimeError(f"pop_() list index must be an integer, got '{get_type_name(idx)}'", line=line, column=col, source_code=interpreter.source_code)
        resolved_idx = len(collection) + idx if idx < 0 else idx
        if 0 <= resolved_idx < len(collection):
            collection.pop(resolved_idx)
            return None
        raise FlowRuntimeError(f"pop_() index out of range: {idx}", line=line, column=col, source_code=interpreter.source_code)

    if isinstance(collection, (FlowDict, dict)):
        if len(args) != 2:
            raise FlowRuntimeError("pop_() on dict requires a key argument", line=line, column=col, source_code=interpreter.source_code)
        key = args[1]
        if key not in collection:
            raise FlowRuntimeError(f"KeyError: key {stringify_value(key)} not found in dictionary", line=line, column=col, source_code=interpreter.source_code)
        del collection[key]
        return None

    raise FlowRuntimeError(f"pop_() requires a mutable list or dict, got '{get_type_name(collection)}'", line=line, column=col, source_code=interpreter.source_code)


def fn_clear(interpreter: Any, args: list[Any], line: int, col: int) -> None:
    if len(args) != 1:
        raise FlowRuntimeError(f"clear_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    if isinstance(collection, (list, FlowDict, dict)):
        collection.clear()
        return None
    raise FlowRuntimeError(f"clear_() requires a mutable list or dict, got '{get_type_name(collection)}'", line=line, column=col, source_code=interpreter.source_code)


# ------------------ String Functions (11) ------------------

def fn_lower(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 1:
        raise FlowRuntimeError(f"lower_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "lower_", line, col, interpreter.source_code)
    return args[0].lower()


def fn_upper(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 1:
        raise FlowRuntimeError(f"upper_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "upper_", line, col, interpreter.source_code)
    return args[0].upper()


def fn_capitalize(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 1:
        raise FlowRuntimeError(f"capitalize_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "capitalize_", line, col, interpreter.source_code)
    return args[0].capitalize()


def fn_title(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 1:
        raise FlowRuntimeError(f"title_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "title_", line, col, interpreter.source_code)
    return args[0].title()


def fn_strip(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 1:
        raise FlowRuntimeError(f"strip_() expected 1 argument, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "strip_", line, col, interpreter.source_code)
    return args[0].strip()


def fn_replace(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 3:
        raise FlowRuntimeError(f"replace_() expected 3 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "replace_", line, col, interpreter.source_code)
    old = _to_str(args[1])
    new = _to_str(args[2])
    return args[0].replace(old, new)


def fn_find(interpreter: Any, args: list[Any], line: int, col: int) -> int:
    if len(args) != 2:
        raise FlowRuntimeError(f"find_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "find_", line, col, interpreter.source_code)
    sub = _to_str(args[1])
    return args[0].find(sub)


def fn_startswith(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
    if len(args) != 2:
        raise FlowRuntimeError(f"startswith_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "startswith_", line, col, interpreter.source_code)
    prefix = _to_str(args[1])
    return args[0].startswith(prefix)


def fn_endswith(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
    if len(args) != 2:
        raise FlowRuntimeError(f"endswith_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "endswith_", line, col, interpreter.source_code)
    suffix = _to_str(args[1])
    return args[0].endswith(suffix)


def fn_split(interpreter: Any, args: list[Any], line: int, col: int) -> list:
    if len(args) not in (1, 2):
        raise FlowRuntimeError(f"split_() expected 1 or 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    _check_str(args[0], "split_", line, col, interpreter.source_code)
    s = args[0]
    sep = _to_str(args[1]) if len(args) == 2 else None
    return s.split(sep)


def fn_join(interpreter: Any, args: list[Any], line: int, col: int) -> str:
    if len(args) != 2:
        raise FlowRuntimeError(f"join_() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=interpreter.source_code)
    collection = args[0]
    _check_col(collection, "join_", line, col, interpreter.source_code)
    sep = _to_str(args[1])
    return sep.join(stringify_value(item) for item in collection)


FLOWLIB_FUNCTIONS: dict[str, BuiltinFunction] = {
    # 13 Collection functions
    "min_": BuiltinFunction("min_", fn_min, expected_arity=1),
    "max_": BuiltinFunction("max_", fn_max, expected_arity=1),
    "sum_": BuiltinFunction("sum_", fn_sum, expected_arity=None),
    "asort_": BuiltinFunction("asort_", fn_asort, expected_arity=1),
    "dsort_": BuiltinFunction("dsort_", fn_dsort, expected_arity=1),
    "rev_": BuiltinFunction("rev_", fn_rev, expected_arity=1),
    "all_": BuiltinFunction("all_", fn_all, expected_arity=1),
    "any_": BuiltinFunction("any_", fn_any, expected_arity=1),
    "count_": BuiltinFunction("count_", fn_count, expected_arity=2),
    "index_": BuiltinFunction("index_", fn_index, expected_arity=2),
    "get_": BuiltinFunction("get_", fn_get, expected_arity=None),
    "pop_": BuiltinFunction("pop_", fn_pop, expected_arity=None),
    "clear_": BuiltinFunction("clear_", fn_clear, expected_arity=1),
    # 11 String functions
    "lower_": BuiltinFunction("lower_", fn_lower, expected_arity=1),
    "upper_": BuiltinFunction("upper_", fn_upper, expected_arity=1),
    "capitalize_": BuiltinFunction("capitalize_", fn_capitalize, expected_arity=1),
    "title_": BuiltinFunction("title_", fn_title, expected_arity=1),
    "strip_": BuiltinFunction("strip_", fn_strip, expected_arity=1),
    "replace_": BuiltinFunction("replace_", fn_replace, expected_arity=3),
    "find_": BuiltinFunction("find_", fn_find, expected_arity=2),
    "startswith_": BuiltinFunction("startswith_", fn_startswith, expected_arity=2),
    "endswith_": BuiltinFunction("endswith_", fn_endswith, expected_arity=2),
    "split_": BuiltinFunction("split_", fn_split, expected_arity=None),
    "join_": BuiltinFunction("join_", fn_join, expected_arity=2),
}

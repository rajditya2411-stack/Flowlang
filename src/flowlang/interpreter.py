"""FlowLang Tree-Walk Interpreter for FlowLang V1.

Executes FlowLang V1 AST nodes, managing runtime environments, control flow
(if/elif/else, while, do-while, for), function calls (dfn/return),
static and dynamic typing, float division, and string operations.
"""

from typing import Any, Callable, Optional
from flowlang.ast import (
    Program,
    Statement,
    Expression,
    ExpressionStatement,
    VariableDeclaration,
    Block,
    IfStatement,
    WhileStatement,
    DoWhileStatement,
    ForStatement,
    ForInStatement,
    FunctionDeclaration,
    ReturnStatement,
    ImportStatement,
    Assignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    ListLiteral,
    BrackLiteral,
    DictLiteral,
    StructLiteral,
    IndexAccess,
    IndexAssignment,
    MemberAccess,
    CompoundAssignment,
    NumberLiteral,
    StringLiteral,
    CharLiteral,
    BooleanLiteral,
    Identifier,
    BreakStatement,
    ContinueStatement,
    StructDeclaration,
    EnumDeclaration,
    TryCatchStatement,
    RaiseStatement,
    GlobalStatement,
)
import math
from flowlang.runtime import (
    Environment,
    FlowCallable,
    BuiltinFunction,
    UserFunction,
    ReturnSignal,
    UserRaiseSignal,
    Char,
    Brack,
    FlowDict,
    DictKeysView,
    DictValuesView,
    StructType,
    StructInstance,
    EnumType,
    EnumValue,
    validate_dict_key,
    make_independent_copy,
    deep_freeze,
    parse_bk_input,
    stringify_value,
    get_type_name,
    check_type_match,
)
from flowlang.errors import FlowRuntimeError
from flowlang.flowlib import FLOWLIB_FUNCTIONS

INT32_MIN = -2147483648
INT32_MAX = 2147483647


class BreakSignal(Exception):
    """Raised by break to terminate loop."""
    pass


class ContinueSignal(Exception):
    """Raised by continue to jump to next loop iteration."""
    pass


def check_int32_overflow(val: int, line: int, column: int, source_code: Optional[str]) -> int:
    if val < INT32_MIN or val > INT32_MAX:
        raise FlowRuntimeError(
            f"Integer overflow: result {val} exceeds 32-bit signed integer range (-2147483648 to 2147483647)",
            line=line,
            column=column,
            source_code=source_code,
        )
    return val


STDLIB_MODULES: dict[str, dict[str, BuiltinFunction]] = {
    "flowlib": FLOWLIB_FUNCTIONS,
}


class Interpreter:
    """Evaluates FlowLang V1 AST nodes."""

    def __init__(
        self,
        globals_env: Optional[Environment] = None,
        output_handler: Optional[Callable[[str], None]] = None,
        input_handler: Optional[Callable[[str], str]] = None,
        source_code: Optional[str] = None,
    ):
        self.source_code = source_code
        self.output_handler = output_handler or print
        self.input_handler = input_handler or input
        if globals_env is not None:
            self.globals = globals_env
        else:
            self.globals = Environment()
            self._init_builtins()
        self.environment = self.globals
        self.call_depth = 0
        import sys
        if sys.getrecursionlimit() < 10000:
            sys.setrecursionlimit(10000)

    def _init_builtins(self) -> None:
        """Register built-in functions in the global environment."""

        # say(*args)
        def builtin_say(interpreter: Any, args: list[Any], line: int, col: int) -> None:
            text = " ".join(stringify_value(arg) for arg in args)
            self.output_handler(text)
            return None

        # pow_(base, exp)
        def builtin_pow(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
            if len(args) != 2:
                raise FlowRuntimeError(
                    f"pow_ expected 2 arguments, got {len(args)}",
                    line=line,
                    column=col,
                    source_code=self.source_code,
                )
            base, exp = args[0], args[1]
            if not isinstance(base, (int, float)) or isinstance(base, bool) or \
               not isinstance(exp, (int, float)) or isinstance(exp, bool):
                raise FlowRuntimeError(
                    "pow_ arguments must be numbers",
                    line=line,
                    column=col,
                    source_code=self.source_code,
                )
            res = base ** exp
            if isinstance(base, int) and isinstance(exp, int) and exp >= 0:
                return check_int32_overflow(int(res), line, col, self.source_code)
            return float(res)

        # input(prompt="")
        def builtin_input(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            prompt = stringify_value(args[0]) if args else ""
            try:
                return self.input_handler(prompt)
            except EOFError:
                return ""

        # int_(x) / int(x)
        def builtin_int(interpreter: Any, args: list[Any], line: int, col: int) -> int:
            if len(args) != 1:
                raise FlowRuntimeError("int_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, bool):
                raise FlowRuntimeError("int_() cannot convert bool to int", line=line, column=col, source_code=self.source_code)
            if isinstance(val, EnumValue):
                raise FlowRuntimeError("int_() cannot convert enum to int (enums are opaque in FlowLang)", line=line, column=col, source_code=self.source_code)
            if isinstance(val, Char):
                raise FlowRuntimeError("int_() cannot convert char to int", line=line, column=col, source_code=self.source_code)
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                import math
                if val >= 0:
                    floor_v = math.floor(val)
                    frac = val - floor_v
                    if frac <= 0.5 + 1e-12:
                        return int(floor_v)
                    return int(floor_v + 1)
                else:
                    abs_v = abs(val)
                    floor_v = math.floor(abs_v)
                    frac = abs_v - floor_v
                    if frac <= 0.5 + 1e-12:
                        return -int(floor_v)
                    return -int(floor_v + 1)
            if isinstance(val, str):
                try:
                    if "." in val:
                        flt_val = float(val)
                        return builtin_int(interpreter, [flt_val], line, col)
                    return int(val)
                except ValueError:
                    raise FlowRuntimeError(f"invalid literal for int_(): {val!r}", line=line, column=col, source_code=self.source_code)
            raise FlowRuntimeError(f"Cannot convert type '{get_type_name(val)}' to int", line=line, column=col, source_code=self.source_code)

        # flt_(x) / flt(x)
        def builtin_flt(interpreter: Any, args: list[Any], line: int, col: int) -> float:
            if len(args) != 1:
                raise FlowRuntimeError("flt_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, bool):
                raise FlowRuntimeError("flt_() cannot convert bool to flt", line=line, column=col, source_code=self.source_code)
            if isinstance(val, Char):
                raise FlowRuntimeError("flt_() cannot convert char to flt", line=line, column=col, source_code=self.source_code)
            try:
                return float(val)
            except (ValueError, TypeError):
                raise FlowRuntimeError(f"could not convert to flt: {val!r}", line=line, column=col, source_code=self.source_code)

        # str_(x) / str(x)
        def builtin_str(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            if len(args) != 1:
                raise FlowRuntimeError("str_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            if isinstance(args[0], EnumValue):
                return args[0].member
            return stringify_value(args[0])

        # bool_(x) / bool(x)
        def builtin_bool(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
            if len(args) != 1:
                raise FlowRuntimeError("bool_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                lower = val.strip().lower()
                if lower == "true":
                    return True
                if lower == "false":
                    return False
            raise FlowRuntimeError(
                f"Cannot convert type '{get_type_name(val)}' to bool (bool_() only accepts bool or 'true'/'false')",
                line=line,
                column=col,
                source_code=self.source_code,
            )

        # type_(x)
        def builtin_type(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            if len(args) != 1:
                raise FlowRuntimeError("type_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            return get_type_name(args[0])

        # len_(collection)
        def builtin_len(interpreter: Any, args: list[Any], line: int, col: int) -> int:
            if len(args) != 1:
                raise FlowRuntimeError("len_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, (list, Brack, tuple, FlowDict, dict, str)):
                return len(val)
            raise FlowRuntimeError(f"len_() not supported for type '{get_type_name(val)}'", line=line, column=col, source_code=self.source_code)

        # append_(list, value)
        def builtin_append(interpreter: Any, args: list[Any], line: int, col: int) -> None:
            if len(args) != 2:
                raise FlowRuntimeError(f"append_() takes exactly 2 arguments, got {len(args)}", line=line, column=col, source_code=self.source_code)
            lst, item = args[0], args[1]
            if not isinstance(lst, list):
                raise FlowRuntimeError(f"append_() requires a mutable list, got '{get_type_name(lst)}'", line=line, column=col, source_code=self.source_code)
            lst.append(item)
            return None

        # listb_(brack)
        def builtin_listb(interpreter: Any, args: list[Any], line: int, col: int) -> list:
            if len(args) != 1:
                raise FlowRuntimeError("listb_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, (Brack, tuple, list)):
                return list(val)
            raise FlowRuntimeError(f"listb_() expected brack or list, got '{get_type_name(val)}'", line=line, column=col, source_code=self.source_code)

        # freeze_(list)
        def builtin_freeze(interpreter: Any, args: list[Any], line: int, col: int) -> Brack:
            if len(args) != 1:
                raise FlowRuntimeError("freeze_() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, (list, Brack, tuple)):
                return deep_freeze(val)
            raise FlowRuntimeError(f"freeze_() expected list or brack, got '{get_type_name(val)}'", line=line, column=col, source_code=self.source_code)

        # bk(input) - collection input parser
        def builtin_bk(interpreter: Any, args: list[Any], line: int, col: int) -> Brack:
            if len(args) != 1:
                raise FlowRuntimeError("bk() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            return parse_bk_input(args[0], line=line, col=col, source_code=self.source_code)

        # min(a, b)
        def builtin_min(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
            if len(args) != 2:
                raise FlowRuntimeError(f"min() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=self.source_code)
            a, b = args[0], args[1]
            if not isinstance(a, (int, float)) or isinstance(a, bool) or not isinstance(b, (int, float)) or isinstance(b, bool):
                raise FlowRuntimeError("min() arguments must be numbers", line=line, column=col, source_code=self.source_code)
            return a if a < b else b

        # max(a, b)
        def builtin_max(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
            if len(args) != 2:
                raise FlowRuntimeError(f"max() expected 2 arguments, got {len(args)}", line=line, column=col, source_code=self.source_code)
            a, b = args[0], args[1]
            if not isinstance(a, (int, float)) or isinstance(a, bool) or not isinstance(b, (int, float)) or isinstance(b, bool):
                raise FlowRuntimeError("max() arguments must be numbers", line=line, column=col, source_code=self.source_code)
            return a if a > b else b

        self.globals.define("say", BuiltinFunction("say", builtin_say, expected_arity=None))
        self.globals.define("pow_", BuiltinFunction("pow_", builtin_pow, expected_arity=2))
        self.globals.define("input", BuiltinFunction("input", builtin_input, expected_arity=None))
        self.globals.define("int", BuiltinFunction("int", builtin_int, expected_arity=1))
        self.globals.define("int_", BuiltinFunction("int_", builtin_int, expected_arity=1))
        self.globals.define("flt", BuiltinFunction("flt", builtin_flt, expected_arity=1))
        self.globals.define("flt_", BuiltinFunction("flt_", builtin_flt, expected_arity=1))
        self.globals.define("str", BuiltinFunction("str", builtin_str, expected_arity=1))
        self.globals.define("str_", BuiltinFunction("str_", builtin_str, expected_arity=1))
        self.globals.define("bool", BuiltinFunction("bool", builtin_bool, expected_arity=1))
        self.globals.define("bool_", BuiltinFunction("bool_", builtin_bool, expected_arity=1))
        self.globals.define("type", BuiltinFunction("type", builtin_type, expected_arity=1))
        self.globals.define("type_", BuiltinFunction("type_", builtin_type, expected_arity=1))
        self.globals.define("len_", BuiltinFunction("len_", builtin_len, expected_arity=1))
        self.globals.define("append_", BuiltinFunction("append_", builtin_append, expected_arity=2))
        self.globals.define("listb_", BuiltinFunction("listb_", builtin_listb, expected_arity=1))
        self.globals.define("freeze_", BuiltinFunction("freeze_", builtin_freeze, expected_arity=1))
        self.globals.define("bk", BuiltinFunction("bk", builtin_bk, expected_arity=1))
        self.globals.define("min", BuiltinFunction("min", builtin_min, expected_arity=2))
        self.globals.define("max", BuiltinFunction("max", builtin_max, expected_arity=2))
        self.globals.define("none", None, type_name="lit")

    # ------------------ Execution Entry Points ------------------

    def _evaluate_condition(self, expr: Expression) -> bool:
        cond = self.evaluate(expr)
        if not isinstance(cond, bool):
            raise FlowRuntimeError(
                f"Condition must evaluate to a boolean, got '{get_type_name(cond)}'",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )
        return cond

    def _get_static_type(self, expr: Expression) -> Optional[str]:
        curr = expr
        while isinstance(curr, Grouping):
            curr = curr.expression
        if isinstance(curr, Identifier):
            return self.environment.get_type(curr.name)
        if isinstance(curr, CallExpression) and isinstance(curr.callee, Identifier):
            if self.environment._exists(curr.callee.name):
                try:
                    fn = self.environment.get(curr.callee.name, curr.line, curr.column, self.source_code)
                    if isinstance(fn, UserFunction):
                        return fn.return_type
                except Exception:
                    pass
        if isinstance(curr, BinaryOp):
            lt = self._get_static_type(curr.left)
            rt = self._get_static_type(curr.right)
            if lt == "lit" and rt == "lit":
                return "lit"
        return None

    def _is_lit_operand(self, expr: Expression) -> bool:
        return self._get_static_type(expr) == "lit"

    def _check_lit_to_static_assignment(self, target_name: str, target_type: str, init_expr: Expression, line: int, column: int) -> None:
        curr = init_expr
        while isinstance(curr, Grouping):
            curr = curr.expression
        if isinstance(curr, Identifier):
            src_var_type = self.environment.get_type(curr.name)
            if src_var_type == "lit":
                raise FlowRuntimeError(
                    f"Cannot directly assign 'lit' variable '{curr.name}' to statically typed variable '{target_name}' of type '{target_type}' without explicit conversion (use {target_type}_())",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
        elif isinstance(curr, CallExpression) and isinstance(curr.callee, Identifier):
            if self.environment._exists(curr.callee.name):
                try:
                    fn = self.environment.get(curr.callee.name, line, column, self.source_code)
                    if isinstance(fn, UserFunction) and fn.return_type == "lit":
                        raise FlowRuntimeError(
                            f"Cannot directly assign result of function '{curr.callee.name}' returning 'lit' to statically typed variable '{target_name}' of type '{target_type}' without explicit conversion (use {target_type}_())",
                            line=line,
                            column=column,
                            source_code=self.source_code,
                        )
                except FlowRuntimeError:
                    raise
                except Exception:
                    pass

    def interpret(self, program: Program) -> Any:
        try:
            last_value = None
            for stmt in program.statements:
                last_value = self.execute(stmt)
            return last_value
        except RecursionError:
            raise FlowRuntimeError(
                "Maximum recursion depth exceeded",
                line=program.line,
                column=program.column,
                source_code=self.source_code,
            )

    def execute(self, stmt: Statement) -> Any:
        if isinstance(stmt, ExpressionStatement):
            return self.evaluate(stmt.expression)

        if isinstance(stmt, BreakStatement):
            raise BreakSignal()

        if isinstance(stmt, ContinueStatement):
            raise ContinueSignal()

        if isinstance(stmt, StructDeclaration):
            struct_type = StructType(name=stmt.name, fields=stmt.fields)
            self.environment.define_struct(stmt.name, struct_type, line=stmt.line, column=stmt.column, source_code=self.source_code)
            return None

        if isinstance(stmt, EnumDeclaration):
            enum_type = EnumType(name=stmt.name, members=stmt.members)
            self.environment.define_enum(stmt.name, enum_type, line=stmt.line, column=stmt.column, source_code=self.source_code)
            return None

        if isinstance(stmt, GlobalStatement):
            fn_env = self.environment.get_enclosing_function_env()
            if fn_env is not None:
                fn_env.declare_global(stmt.name)
            return None

        if isinstance(stmt, RaiseStatement):
            err_msg = self.evaluate(stmt.expression)
            if not isinstance(err_msg, str):
                raise FlowRuntimeError(
                    f"Raise expression must evaluate to a string, got '{get_type_name(err_msg)}'",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
            raise UserRaiseSignal(err_msg, line=stmt.line, column=stmt.column)

        if isinstance(stmt, TryCatchStatement):
            previous_env = self.environment
            try:
                try_env = Environment(parent=self.environment)
                self.execute_block(stmt.try_block.statements, try_env)
            except UserRaiseSignal as u_sig:
                catch_env = Environment(parent=previous_env)
                catch_env.define(stmt.error_name, u_sig.message, type_name="str", is_mutable=False, line=stmt.line, column=stmt.column, source_code=self.source_code)
                self.execute_block(stmt.catch_block.statements, catch_env)
            except FlowRuntimeError as r_err:
                catch_env = Environment(parent=previous_env)
                catch_env.define(stmt.error_name, r_err.message, type_name="str", is_mutable=False, line=stmt.line, column=stmt.column, source_code=self.source_code)
                self.execute_block(stmt.catch_block.statements, catch_env)
            finally:
                self.environment = previous_env
            return None

        if isinstance(stmt, VariableDeclaration):
            enum_type = self.environment.get_enum(stmt.type_name)
            if enum_type is not None:
                value = self.evaluate(stmt.initializer)
                if not (isinstance(value, EnumValue) and value.enum_type.name == stmt.type_name):
                    raise FlowRuntimeError(
                        f"Type mismatch: cannot initialize variable '{stmt.name}' of type '{stmt.type_name}' with value of type '{get_type_name(value)}'",
                        line=stmt.line,
                        column=stmt.column,
                        source_code=self.source_code,
                    )
                self.environment.define(
                    stmt.name,
                    value,
                    type_name=stmt.type_name,
                    is_mutable=stmt.is_mutable,
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
                return None

            struct_type = self.environment.get_struct(stmt.type_name)
            if struct_type is not None:
                if isinstance(stmt.initializer, StructLiteral):
                    raw_values = [self.evaluate(v) for v in stmt.initializer.values]
                    if len(raw_values) != len(struct_type.fields):
                        raise FlowRuntimeError(
                            f"Struct '{stmt.type_name}' expects {len(struct_type.fields)} fields, got {len(raw_values)}",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )
                    fields_dict = {}
                    for (f_name, f_type), val in zip(struct_type.fields, raw_values):
                        if not check_type_match(f_type, val):
                            raise FlowRuntimeError(
                                f"Type mismatch for field '{f_name}' in struct '{stmt.type_name}': expected '{f_type}', got '{get_type_name(val)}'",
                                line=stmt.line,
                                column=stmt.column,
                                source_code=self.source_code,
                            )
                        fields_dict[f_name] = val
                    value = StructInstance(struct_type, fields_dict)
                else:
                    value = self.evaluate(stmt.initializer)
                    if not isinstance(value, StructInstance) or value.struct_type.name != stmt.type_name:
                        raise FlowRuntimeError(
                            f"Type mismatch: cannot initialize variable '{stmt.name}' of type '{stmt.type_name}' with value of type '{get_type_name(value)}'",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )
            else:
                if stmt.type_name != "lit":
                    self._check_lit_to_static_assignment(stmt.name, stmt.type_name, stmt.initializer, stmt.line, stmt.column)

                value = self.evaluate(stmt.initializer)

                if stmt.type_name == "lit":
                    if isinstance(value, list):
                        raise FlowRuntimeError(
                            f"Variable '{stmt.name}' declared as 'lit' cannot directly hold a mutable list (use freeze_() to store as immutable brack)",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, StructInstance):
                        raise FlowRuntimeError(
                            f"Variable '{stmt.name}' declared as 'lit' cannot hold a struct instance",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, EnumValue):
                        raise FlowRuntimeError(
                            f"Variable '{stmt.name}' declared as 'lit' cannot hold an enum value",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, FlowCallable):
                        raise FlowRuntimeError(
                            f"Variable '{stmt.name}' declared as 'lit' cannot hold a function (use 'func' type)",
                            line=stmt.line,
                            column=stmt.column,
                            source_code=self.source_code,
                        )

            self.environment.define(
                name=stmt.name,
                value=value,
                type_name=stmt.type_name,
                is_mutable=stmt.is_mutable,
                line=stmt.line,
                column=stmt.column,
                source_code=self.source_code,
            )
            return None

        if isinstance(stmt, Block):
            return self.execute_block(stmt.statements, Environment(parent=self.environment))

        if isinstance(stmt, IfStatement):
            if self._evaluate_condition(stmt.condition):
                return self.execute(stmt.then_branch)
            elif stmt.else_branch is not None:
                return self.execute(stmt.else_branch)
            return None

        if isinstance(stmt, WhileStatement):
            last_value = None
            while self._evaluate_condition(stmt.condition):
                try:
                    last_value = self.execute(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return last_value

        if isinstance(stmt, DoWhileStatement):
            last_value = None
            try:
                last_value = self.execute(stmt.body)
            except BreakSignal:
                return last_value
            except ContinueSignal:
                pass

            while self._evaluate_condition(stmt.condition):
                try:
                    last_value = self.execute(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return last_value

        if isinstance(stmt, ForStatement):
            loop_env = Environment(parent=self.environment)
            init_val = self.evaluate(stmt.init_expr)
            loop_env.define(stmt.target, init_val, type_name=get_type_name(init_val), is_mutable=True, line=stmt.line, column=stmt.column, source_code=self.source_code)

            previous_env = self.environment
            try:
                self.environment = loop_env
                last_val = None
                while self._evaluate_condition(stmt.condition):
                    try:
                        last_val = self.execute(stmt.body)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
                    self.evaluate(stmt.update)
                return last_val
            finally:
                self.environment = previous_env

        if isinstance(stmt, ForInStatement):
            col = self.evaluate(stmt.iterable)
            if isinstance(col, (list, Brack, tuple)):
                items = list(col)
            elif isinstance(col, (FlowDict, dict)):
                items = [Brack((k, v)) for k, v in col.items()]
            elif isinstance(col, (DictKeysView, DictValuesView)):
                items = list(col)
            else:
                raise FlowRuntimeError(
                    f"Type '{get_type_name(col)}' is not iterable",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )

            if stmt.range_args is not None:
                start_val = self.evaluate(stmt.range_args[0])
                end_val = self.evaluate(stmt.range_args[1])
                step_val = self.evaluate(stmt.range_args[2]) if len(stmt.range_args) > 2 else 1

                if not isinstance(start_val, int) or isinstance(start_val, bool) or \
                   not isinstance(end_val, int) or isinstance(end_val, bool) or \
                   not isinstance(step_val, int) or isinstance(step_val, bool):
                    raise FlowRuntimeError(
                        "Range arguments must be integers",
                        line=stmt.line,
                        column=stmt.column,
                        source_code=self.source_code,
                    )

                if step_val == 0:
                    raise FlowRuntimeError(
                        "Range step cannot be zero",
                        line=stmt.line,
                        column=stmt.column,
                        source_code=self.source_code,
                    )

                n = len(items)
                def resolve_pos(p: int) -> int:
                    return n + p if p < 0 else p

                start_idx = resolve_pos(start_val)
                end_idx = resolve_pos(end_val)

                if step_val > 0:
                    idx_range = range(start_idx, end_idx + 1, step_val)
                else:
                    idx_range = range(start_idx, end_idx - 1, step_val)

                selected = [items[i] for i in idx_range if 0 <= i < n]
            else:
                selected = items

            loop_env = Environment(parent=self.environment)
            previous_env = self.environment
            try:
                self.environment = loop_env
                last_val = None
                for item in selected:
                    loop_env.values[stmt.target] = make_independent_copy(item)
                    if stmt.target not in loop_env.types:
                        loop_env.types[stmt.target] = get_type_name(item)
                        loop_env.is_mutable[stmt.target] = True
                    try:
                        last_val = self.execute(stmt.body)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        continue
                return last_val
            finally:
                self.environment = previous_env

        if isinstance(stmt, FunctionDeclaration):
            if stmt.name in self.environment.values:
                raise FlowRuntimeError(
                    f"Function '{stmt.name}' is already defined in this scope",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
            fn = UserFunction(
                name=stmt.name,
                parameters=stmt.parameters,
                return_type=stmt.return_type,
                body=stmt.body,
                closure=self.environment,
            )
            self.environment.define(stmt.name, fn, type_name="func", line=stmt.line, column=stmt.column, source_code=self.source_code)
            return None

        if isinstance(stmt, ReturnStatement):
            val = self.evaluate(stmt.expression) if stmt.expression is not None else None
            raise ReturnSignal(val)

        if isinstance(stmt, ImportStatement):
            module_name = stmt.module_name
            if not hasattr(self, "_imported_modules"):
                self._imported_modules = set()
            if module_name in self._imported_modules:
                raise FlowRuntimeError(
                    f"Module '{module_name}' has already been imported",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
            if module_name not in STDLIB_MODULES:
                raise FlowRuntimeError(
                    f"Module '{module_name}' not found",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
            self._imported_modules.add(module_name)
            for fn_name, fn_obj in STDLIB_MODULES[module_name].items():
                self.globals.define(fn_name, fn_obj)
            return None

        raise FlowRuntimeError(
            f"Unknown statement type: {type(stmt).__name__}",
            line=stmt.line,
            column=stmt.column,
            source_code=self.source_code,
        )

    def execute_block(self, statements: list[Statement], block_env: Environment) -> Any:
        previous_env = self.environment
        try:
            self.environment = block_env
            last_value = None
            for stmt in statements:
                last_value = self.execute(stmt)
            return last_value
        finally:
            self.environment = previous_env

    # ------------------ Expression Evaluation ------------------

    def evaluate(self, expr: Expression) -> Any:
        if isinstance(expr, NumberLiteral):
            return expr.value

        if isinstance(expr, StringLiteral):
            return expr.value

        if isinstance(expr, CharLiteral):
            return Char(expr.value)

        if isinstance(expr, BooleanLiteral):
            return expr.value

        if isinstance(expr, Identifier):
            enum_type = self.environment.get_enum(expr.name)
            if enum_type is not None:
                return enum_type
            return self.environment.get(expr.name, expr.line, expr.column, self.source_code)

        if isinstance(expr, Grouping):
            return self.evaluate(expr.expression)

        if isinstance(expr, ListLiteral):
            return [self.evaluate(e) for e in expr.elements]

        if isinstance(expr, BrackLiteral):
            return Brack(self.evaluate(e) for e in expr.elements)

        if isinstance(expr, DictLiteral):
            d = FlowDict()
            for key_expr, val_expr in expr.entries:
                key = self.evaluate(key_expr)
                validate_dict_key(key, key_expr.line, key_expr.column, self.source_code)
                if any(k == key and type(k) is type(key) for k in d.keys()):
                    raise FlowRuntimeError(
                        f"Duplicate dictionary key: {stringify_value(key)}",
                        line=key_expr.line,
                        column=key_expr.column,
                        source_code=self.source_code,
                    )
                val = self.evaluate(val_expr)
                d[key] = val
            return d

        if isinstance(expr, IndexAccess):
            if isinstance(expr.target, Identifier):
                target_type = self.environment.get_type(expr.target.name)
                if target_type == "lit":
                    raise FlowRuntimeError(
                        "Cannot index 'lit' variable directly; explicit conversion is required",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )

            target = self.evaluate(expr.target)
            index = self.evaluate(expr.index)

            if isinstance(target, (list, Brack, tuple)):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise FlowRuntimeError(
                        f"List/brack index must be an integer, got '{get_type_name(index)}'",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                n = len(target)
                if index < -n or index >= n or n == 0:
                    raise FlowRuntimeError(
                        f"Index out of range: index {index} for collection of length {n}",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                return target[index]

            if isinstance(target, str):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise FlowRuntimeError(
                        f"String index must be an integer, got '{get_type_name(index)}'",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                n = len(target)
                if index < -n or index >= n or n == 0:
                    raise FlowRuntimeError(
                        f"Index out of range: index {index} for string of length {n}",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                return target[index]

            if isinstance(target, (FlowDict, dict)):
                validate_dict_key(index, expr.index.line, expr.index.column, self.source_code)
                found = False
                matched_key = None
                for k in target.keys():
                    if k == index and type(k) is type(index):
                        found = True
                        matched_key = k
                        break
                if not found:
                    raise FlowRuntimeError(
                        f"KeyError: key {stringify_value(index)} not found in dictionary",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                return target[matched_key]

            raise FlowRuntimeError(
                f"Type '{get_type_name(target)}' is not indexable",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(expr, IndexAssignment):
            target = self.evaluate(expr.target)
            index = self.evaluate(expr.index)
            value = self.evaluate(expr.value)

            if isinstance(target, list):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise FlowRuntimeError(
                        f"List index must be an integer, got '{get_type_name(index)}'",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                n = len(target)
                if index < -n or index >= n or n == 0:
                    raise FlowRuntimeError(
                        f"Index out of range: index {index} for list of length {n}",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                target[index] = value
                return value

            if isinstance(target, str):
                raise FlowRuntimeError(
                    "Cannot modify immutable string: strings do not support item assignment",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )

            if isinstance(target, (Brack, tuple)):
                raise FlowRuntimeError(
                    "Cannot modify immutable brack: bracks do not support item assignment",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )

            if isinstance(target, (FlowDict, dict)):
                validate_dict_key(index, expr.index.line, expr.index.column, self.source_code)
                for k in list(target.keys()):
                    if k == index and type(k) is not type(index):
                        del target[k]
                target[index] = value
                return value

            raise FlowRuntimeError(
                f"Type '{get_type_name(target)}' does not support index assignment",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(expr, CompoundAssignment):
            op_map = {
                "+=": "+",
                "-=": "-",
                "*=": "*",
                "//=": "//",
                "%=": "%",
            }
            base_op = op_map[expr.operator]
            rhs_val = self.evaluate(expr.value)

            if isinstance(expr.target, Identifier):
                target_type = self.environment.get_type(expr.target.name)
                rhs_is_lit = self._is_lit_operand(expr.value)
                lhs_is_lit = (target_type == "lit")
                if lhs_is_lit != rhs_is_lit:
                    raise FlowRuntimeError(
                        f"Cannot perform compound assignment '{expr.operator}' between 'lit' and concrete type without explicit conversion",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                curr_val = self.environment.get(expr.target.name, expr.line, expr.column, self.source_code)
                new_val = self._apply_binary_op(base_op, curr_val, rhs_val, expr.line, expr.column)
                self.environment.assign(expr.target.name, new_val, expr.line, expr.column, self.source_code)
                return new_val

            if isinstance(expr.target, IndexAccess):
                target = self.evaluate(expr.target.target)
                index = self.evaluate(expr.target.index)
                if isinstance(target, list):
                    if not isinstance(index, int) or isinstance(index, bool):
                        raise FlowRuntimeError(
                            f"List index must be an integer, got '{get_type_name(index)}'",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    n = len(target)
                    if index < -n or index >= n or n == 0:
                        raise FlowRuntimeError(
                            f"Index out of range: index {index} for list of length {n}",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    curr_val = target[index]
                    new_val = self._apply_binary_op(base_op, curr_val, rhs_val, expr.line, expr.column)
                    target[index] = new_val
                    return new_val

                if isinstance(target, (FlowDict, dict)):
                    validate_dict_key(index, expr.target.index.line, expr.target.index.column, self.source_code)
                    found = False
                    matched_key = None
                    for k in target.keys():
                        if k == index and type(k) is type(index):
                            found = True
                            matched_key = k
                            break
                    if not found:
                        raise FlowRuntimeError(
                            f"KeyError: key {stringify_value(index)} not found in dictionary",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    curr_val = target[matched_key]
                    new_val = self._apply_binary_op(base_op, curr_val, rhs_val, expr.line, expr.column)
                    target[matched_key] = new_val
                    return new_val

                raise FlowRuntimeError(
                    f"Type '{get_type_name(target)}' does not support index compound assignment",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )

            raise FlowRuntimeError(
                f"Invalid target for compound assignment: {type(expr.target).__name__}",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(expr, StructLiteral):
            if expr.struct_name:
                struct_type = self.environment.get_struct(expr.struct_name)
                if struct_type is None:
                    raise FlowRuntimeError(
                        f"Unknown struct type '{expr.struct_name}'",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                raw_values = [self.evaluate(v) for v in expr.values]
                if len(raw_values) != len(struct_type.fields):
                    raise FlowRuntimeError(
                        f"Struct '{expr.struct_name}' expects {len(struct_type.fields)} fields, got {len(raw_values)}",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                fields_dict = {}
                for (f_name, f_type), val in zip(struct_type.fields, raw_values):
                    if not check_type_match(f_type, val):
                        raise FlowRuntimeError(
                            f"Type mismatch for field '{f_name}' in struct '{expr.struct_name}': expected '{f_type}', got '{get_type_name(val)}'",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    fields_dict[f_name] = val
                return StructInstance(struct_type, fields_dict)
            return [self.evaluate(v) for v in expr.values]

        if isinstance(expr, MemberAccess):
            target = self.evaluate(expr.target)
            member = expr.member
            if isinstance(target, EnumType):
                if member in target.members:
                    return EnumValue(target, member, target.members.index(member))
                raise FlowRuntimeError(
                    f"Enum '{target.name}' has no member '{member}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if isinstance(target, list):
                if member == "clone":
                    return make_independent_copy(target)
            if isinstance(target, StructInstance):
                if member in target.fields:
                    return target.fields[member]
                raise FlowRuntimeError(
                    f"Struct '{target.struct_type.name}' has no field '{member}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if isinstance(target, (FlowDict, dict)):
                if member == "keys":
                    return DictKeysView(target)
                if member == "values":
                    return DictValuesView(target)
            raise FlowRuntimeError(
                f"Type '{get_type_name(target)}' has no member '{member}'",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(expr, UnaryOp):
            return self._evaluate_unary(expr)

        if isinstance(expr, BinaryOp):
            return self._evaluate_binary(expr)

        if isinstance(expr, LogicalOp):
            return self._evaluate_logical(expr)

        if isinstance(expr, Assignment):
            target_type = self.environment.get_type(expr.name)
            struct_type = self.environment.get_struct(target_type) if target_type else None
            if struct_type is not None and isinstance(expr.value, StructLiteral):
                raw_values = [self.evaluate(v) for v in expr.value.values]
                if len(raw_values) != len(struct_type.fields):
                    raise FlowRuntimeError(
                        f"Struct '{target_type}' expects {len(struct_type.fields)} fields, got {len(raw_values)}",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                fields_dict = {}
                for (f_name, f_type), val in zip(struct_type.fields, raw_values):
                    if not check_type_match(f_type, val):
                        raise FlowRuntimeError(
                            f"Type mismatch for field '{f_name}' in struct '{target_type}': expected '{f_type}', got '{get_type_name(val)}'",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    fields_dict[f_name] = val
                value = StructInstance(struct_type, fields_dict)
            else:
                if target_type is not None and target_type != "lit":
                    self._check_lit_to_static_assignment(expr.name, target_type, expr.value, expr.line, expr.column)

                value = self.evaluate(expr.value)

                if target_type == "lit":
                    if isinstance(value, list):
                        raise FlowRuntimeError(
                            f"Variable '{expr.name}' declared as 'lit' cannot directly hold a mutable list (use freeze_() to store as immutable brack)",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, StructInstance):
                        raise FlowRuntimeError(
                            f"Variable '{expr.name}' declared as 'lit' cannot hold a struct instance",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, EnumValue):
                        raise FlowRuntimeError(
                            f"Variable '{expr.name}' declared as 'lit' cannot hold an enum value",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )
                    if isinstance(value, FlowCallable):
                        raise FlowRuntimeError(
                            f"Variable '{expr.name}' declared as 'lit' cannot hold a function (use 'func' type)",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )

            self.environment.assign(expr.name, value, expr.line, expr.column, self.source_code)
            return value

        if isinstance(expr, CallExpression):
            return self._evaluate_call(expr)

        raise FlowRuntimeError(
            f"Unknown expression type: {type(expr).__name__}",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_unary(self, expr: UnaryOp) -> Any:
        operand = self.evaluate(expr.operand)

        if expr.operator == "-":
            if not isinstance(operand, (int, float)) or isinstance(operand, bool):
                raise FlowRuntimeError(
                    f"Operand for unary '-' must be a number, got {get_type_name(operand)}",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if isinstance(operand, int):
                res = -operand
                return check_int32_overflow(res, expr.line, expr.column, self.source_code)
            return -operand

        if expr.operator == "not":
            if not isinstance(operand, bool):
                raise FlowRuntimeError(
                    f"Logical operator 'not' requires a boolean operand, got '{get_type_name(operand)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return not operand

        raise FlowRuntimeError(
            f"Unknown unary operator '{expr.operator}'",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_logical(self, expr: LogicalOp) -> Any:
        left = self.evaluate(expr.left)

        if expr.operator == "or":
            if not isinstance(left, bool):
                raise FlowRuntimeError(
                    f"Logical operator 'or' requires boolean operands, got '{get_type_name(left)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if left:
                return True
            right = self.evaluate(expr.right)
            if not isinstance(right, bool):
                raise FlowRuntimeError(
                    f"Logical operator 'or' requires boolean operands, got '{get_type_name(right)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return right

        if expr.operator == "and":
            if not isinstance(left, bool):
                raise FlowRuntimeError(
                    f"Logical operator 'and' requires boolean operands, got '{get_type_name(left)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if not left:
                return False
            right = self.evaluate(expr.right)
            if not isinstance(right, bool):
                raise FlowRuntimeError(
                    f"Logical operator 'and' requires boolean operands, got '{get_type_name(right)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return right

        raise FlowRuntimeError(
            f"Unknown logical operator '{expr.operator}'",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_binary(self, expr: BinaryOp) -> Any:
        left_type = self._get_static_type(expr.left)
        right_type = self._get_static_type(expr.right)
        left_is_lit = (left_type == "lit")
        right_is_lit = (right_type == "lit")
        left_is_concrete_var = (left_type is not None and left_type != "lit")
        right_is_concrete_var = (right_type is not None and right_type != "lit")

        if (left_is_lit and right_is_concrete_var) or (right_is_lit and left_is_concrete_var):
            if expr.operator == "+":
                left_val = self.evaluate(expr.left)
                right_val = self.evaluate(expr.right)
                if isinstance(left_val, str) or isinstance(right_val, str):
                    raise FlowRuntimeError(
                        "Cannot concatenate 'str' and 'lit' without explicit conversion (use str_())",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                raise FlowRuntimeError(
                    f"Cannot perform '{expr.operator}' between 'lit' and concrete type without explicit conversion",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if expr.operator in ("-", "*", "/", "//", "%"):
                raise FlowRuntimeError(
                    f"Cannot perform '{expr.operator}' between 'lit' and concrete type without explicit conversion",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if expr.operator in ("<", "<=", ">", ">="):
                raise FlowRuntimeError(
                    f"Comparison operator '{expr.operator}' requires operands of same comparable type; cannot compare 'lit' with concrete type without explicit conversion",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            if expr.operator in ("==", "!="):
                raise FlowRuntimeError(
                    f"Operator '{expr.operator}' cannot compare 'lit' with concrete type without explicit conversion",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )

        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        return self._apply_binary_op(expr.operator, left, right, expr.line, expr.column)

    def _apply_binary_op(self, op: str, left: Any, right: Any, line: int, column: int) -> Any:
        # Division: ALWAYS produces float in FlowLang V1
        if op == "/":
            self._check_number_operands(op, left, right, line, column)
            if right == 0:
                raise FlowRuntimeError(
                    "Division by zero",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            return float(left / right)

        # Integer division: // strictly for integers
        if op == "//":
            if not (isinstance(left, int) and not isinstance(left, bool) and isinstance(right, int) and not isinstance(right, bool)):
                raise FlowRuntimeError(
                    f"Operands for '//' must be integers, got '{get_type_name(left)}' and '{get_type_name(right)}'",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            if right == 0:
                raise FlowRuntimeError(
                    "Division by zero",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            res = int(left / right)
            return check_int32_overflow(res, line, column, self.source_code)

        # Modulo: C-style remainder
        if op == "%":
            if not (isinstance(left, int) and not isinstance(left, bool) and isinstance(right, int) and not isinstance(right, bool)):
                raise FlowRuntimeError(
                    f"Operands for '%' must be integers, got '{get_type_name(left)}' and '{get_type_name(right)}'",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            if right == 0:
                raise FlowRuntimeError(
                    "Modulo by zero",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            return int(math.fmod(left, right))

        # Subtraction
        if op == "-":
            self._check_number_operands(op, left, right, line, column)
            if isinstance(left, int) and isinstance(right, int):
                res = left - right
                return check_int32_overflow(res, line, column, self.source_code)
            return float(left - right)

        # Multiplication
        if op == "*":
            # Numbers
            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                if isinstance(left, int) and isinstance(right, int):
                    res = left * right
                    return check_int32_overflow(res, line, column, self.source_code)
                return float(left * right)

            # String * non-negative integer
            if isinstance(left, str) and isinstance(right, int) and not isinstance(right, bool):
                if right < 0:
                    raise FlowRuntimeError(
                        "String multiplication requires a non-negative integer",
                        line=line,
                        column=column,
                        source_code=self.source_code,
                    )
                return left * right

            # non-negative integer * String (symmetric)
            if isinstance(right, str) and isinstance(left, int) and not isinstance(left, bool):
                if left < 0:
                    raise FlowRuntimeError(
                        "String multiplication requires a non-negative integer",
                        line=line,
                        column=column,
                        source_code=self.source_code,
                    )
                return right * left

            raise FlowRuntimeError(
                f"Invalid operands for '*': '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=line,
                column=column,
                source_code=self.source_code,
            )

        # Addition / Concatenation
        if op == "+":
            # Strict boolean isolation: bool cannot be added or concatenated
            if isinstance(left, bool) or isinstance(right, bool):
                raise FlowRuntimeError(
                    "Invalid operands for '+': cannot add or concatenate boolean value",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )

            # Character arithmetic: Char with numbers or Char with Char is invalid in V2
            if isinstance(left, Char) or isinstance(right, Char):
                if isinstance(left, str) or isinstance(right, str):
                    s_left = left.value if isinstance(left, Char) else left
                    s_right = right.value if isinstance(right, Char) else right
                    return s_left + s_right
                raise FlowRuntimeError(
                    "Character arithmetic is not supported in FlowLang V2",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )

            # Numbers
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                if isinstance(left, int) and isinstance(right, int):
                    res = left + right
                    return check_int32_overflow(res, line, column, self.source_code)
                return float(left + right)

            # String concatenation (with str, or str + int/flt)
            if isinstance(left, str) or isinstance(right, str):
                other = right if isinstance(left, str) else left
                if isinstance(other, (list, Brack, tuple, FlowDict, dict)):
                    raise FlowRuntimeError(
                        f"Invalid operands for '+': cannot concatenate 'str' and '{get_type_name(other)}' (use str_() for explicit conversion)",
                        line=line,
                        column=column,
                        source_code=self.source_code,
                    )
                s_left = stringify_value(left) if not isinstance(left, str) else left
                s_right = stringify_value(right) if not isinstance(right, str) else right
                return s_left + s_right

            raise FlowRuntimeError(
                f"Invalid operands for '+': '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=line,
                column=column,
                source_code=self.source_code,
            )

        # Relational comparisons
        if op in (">", ">=", "<", "<="):
            if isinstance(left, (Char, EnumValue)) or isinstance(right, (Char, EnumValue)):
                raise FlowRuntimeError(
                    f"Comparison operator '{op}' requires operands of same comparable type, got '{get_type_name(left)}' and '{get_type_name(right)}'",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )

            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                if op == ">": return left > right
                if op == ">=": return left >= right
                if op == "<": return left < right
                if op == "<=": return left <= right

            if isinstance(left, str) and isinstance(right, str):
                if op == ">": return left > right
                if op == ">=": return left >= right
                if op == "<": return left < right
                if op == "<=": return left <= right

            raise FlowRuntimeError(
                f"Comparison operator '{op}' requires operands of same comparable type, got '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=line,
                column=column,
                source_code=self.source_code,
            )

        # Equality
        if op in ("==", "!="):
            if not self._are_types_comparable(left, right):
                raise FlowRuntimeError(
                    f"Operator '{op}' cannot compare incompatible types '{get_type_name(left)}' and '{get_type_name(right)}'",
                    line=line,
                    column=column,
                    source_code=self.source_code,
                )
            res = (left == right)
            return res if op == "==" else not res

        raise FlowRuntimeError(
            f"Unknown binary operator '{op}'",
            line=line,
            column=column,
            source_code=self.source_code,
        )

    def _are_types_comparable(self, left: Any, right: Any) -> bool:
        if left is None and right is None:
            return True
        if left is None or right is None:
            return False

        if isinstance(left, EnumValue) or isinstance(right, EnumValue):
            return isinstance(left, EnumValue) and isinstance(right, EnumValue) and left.enum_type.name == right.enum_type.name

        left_is_bool = isinstance(left, bool)
        right_is_bool = isinstance(right, bool)
        if left_is_bool or right_is_bool:
            return left_is_bool and right_is_bool

        left_is_num = isinstance(left, (int, float))
        right_is_num = isinstance(right, (int, float))
        if left_is_num or right_is_num:
            return left_is_num and right_is_num

        if isinstance(left, Char) or isinstance(right, Char):
            return isinstance(left, Char) and isinstance(right, Char)

        if isinstance(left, str) or isinstance(right, str):
            return isinstance(left, str) and isinstance(right, str)

        if isinstance(left, list) or isinstance(right, list):
            return isinstance(left, list) and isinstance(right, list)

        if isinstance(left, (Brack, tuple)) or isinstance(right, (Brack, tuple)):
            return isinstance(left, (Brack, tuple)) and isinstance(right, (Brack, tuple))

        if isinstance(left, (FlowDict, dict)) or isinstance(right, (FlowDict, dict)):
            return isinstance(left, (FlowDict, dict)) and isinstance(right, (FlowDict, dict))

        return type(left) is type(right)

    def _evaluate_call(self, expr: CallExpression) -> Any:
        if isinstance(expr.callee, Identifier) and expr.callee.name in ("type_", "type"):
            if len(expr.arguments) != 1:
                raise FlowRuntimeError(
                    f"{expr.callee.name}() takes exactly 1 argument ({len(expr.arguments)} given)",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            arg = expr.arguments[0]
            if isinstance(arg, Identifier):
                if arg.name == "none":
                    return "none"
                var_type = self.environment.get_type(arg.name)
                if var_type is not None:
                    return var_type
                val = self.environment.get(arg.name, arg.line, arg.column, self.source_code)
                return get_type_name(val)
            else:
                val = self.evaluate(arg)
                return get_type_name(val)

        if isinstance(expr.callee, Identifier) and expr.callee.name in ("min", "max", "pow_"):
            for arg in expr.arguments:
                if self._is_lit_operand(arg):
                    raise FlowRuntimeError(
                        f"Cannot pass 'lit' argument to '{expr.callee.name}()' without explicit conversion (use int_() or flt_())",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )

        callee = self.evaluate(expr.callee)

        if not isinstance(callee, FlowCallable):
            name = expr.callee.name if isinstance(expr.callee, Identifier) else str(callee)
            raise FlowRuntimeError(
                f"'{name}' is not callable",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(callee, UserFunction):
            for arg, (param_name, param_type) in zip(expr.arguments, callee.parameters):
                if param_type != "lit":
                    if self._is_lit_operand(arg):
                        arg_name = arg.name if isinstance(arg, Identifier) else "expression"
                        raise FlowRuntimeError(
                            f"Cannot directly pass 'lit' variable '{arg_name}' to parameter '{param_name}' of type '{param_type}' without explicit conversion (use {param_type}_())",
                            line=expr.line,
                            column=expr.column,
                            source_code=self.source_code,
                        )

        args = [self.evaluate(arg) for arg in expr.arguments]
        return callee.call(self, args, expr.line, expr.column)

    # ------------------ Runtime Helpers ------------------

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, Char):
            return True
        return True

    def _check_number_operands(self, operator: str, left: Any, right: Any, line: int, column: int) -> None:
        left_is_num = isinstance(left, (int, float)) and not isinstance(left, bool)
        right_is_num = isinstance(right, (int, float)) and not isinstance(right, bool)
        if not (left_is_num and right_is_num):
            raise FlowRuntimeError(
                f"Operands for '{operator}' must be numbers, got {get_type_name(left)} and {get_type_name(right)}",
                line=line,
                column=column,
                source_code=self.source_code,
            )


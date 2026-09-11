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
    Assignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    ListLiteral,
    BrackLiteral,
    DictLiteral,
    IndexAccess,
    IndexAssignment,
    MemberAccess,
    NumberLiteral,
    StringLiteral,
    CharLiteral,
    BooleanLiteral,
    Identifier,
)
from flowlang.runtime import (
    Environment,
    FlowCallable,
    BuiltinFunction,
    UserFunction,
    ReturnSignal,
    Char,
    Brack,
    FlowDict,
    DictKeysView,
    DictValuesView,
    validate_dict_key,
    make_independent_copy,
    parse_bk_input,
    stringify_value,
    get_type_name,
)
from flowlang.errors import FlowRuntimeError


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
        self.globals = globals_env if globals_env is not None else Environment()
        self.environment = self.globals
        self._init_builtins()

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
                return int(res)
            return float(res)

        # input(prompt="")
        def builtin_input(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            prompt = stringify_value(args[0]) if args else ""
            try:
                return self.input_handler(prompt)
            except EOFError:
                return ""

        # int(x)
        def builtin_int(interpreter: Any, args: list[Any], line: int, col: int) -> int:
            if len(args) != 1:
                raise FlowRuntimeError("int() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            try:
                if isinstance(val, bool):
                    return 1 if val else 0
                return int(val)
            except (ValueError, TypeError):
                raise FlowRuntimeError(f"invalid literal for int(): {val!r}", line=line, column=col, source_code=self.source_code)

        # flt(x)
        def builtin_flt(interpreter: Any, args: list[Any], line: int, col: int) -> float:
            if len(args) != 1:
                raise FlowRuntimeError("flt() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            try:
                return float(val)
            except (ValueError, TypeError):
                raise FlowRuntimeError(f"could not convert to flt: {val!r}", line=line, column=col, source_code=self.source_code)

        # str(x)
        def builtin_str(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            if len(args) != 1:
                raise FlowRuntimeError("str() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            return stringify_value(args[0])

        # char(x)
        def builtin_char(interpreter: Any, args: list[Any], line: int, col: int) -> Char:
            if len(args) != 1:
                raise FlowRuntimeError("char() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, Char):
                return val
            if isinstance(val, str) and len(val) == 1:
                return Char(val)
            raise FlowRuntimeError(
                f"char() expected single character string, got {val!r}",
                line=line,
                column=col,
                source_code=self.source_code,
            )

        # bool(x)
        def builtin_bool(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
            if len(args) != 1:
                raise FlowRuntimeError("bool() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, str):
                lower = val.strip().lower()
                if lower == "true":
                    return True
                if lower == "false":
                    return False
            return self._is_truthy(val)

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

        # remove_(dict, key)
        def builtin_remove(interpreter: Any, args: list[Any], line: int, col: int) -> None:
            if len(args) != 2:
                raise FlowRuntimeError(f"remove_() takes exactly 2 arguments, got {len(args)}", line=line, column=col, source_code=self.source_code)
            d, key = args[0], args[1]
            if not isinstance(d, (FlowDict, dict)):
                raise FlowRuntimeError(f"remove_() requires a dict, got '{get_type_name(d)}'", line=line, column=col, source_code=self.source_code)
            if key not in d:
                raise FlowRuntimeError(f"KeyError: key {stringify_value(key)} not found in dictionary", line=line, column=col, source_code=self.source_code)
            del d[key]
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
                return Brack(val)
            raise FlowRuntimeError(f"freeze_() expected list or brack, got '{get_type_name(val)}'", line=line, column=col, source_code=self.source_code)

        # bk(input) - collection input parser
        def builtin_bk(interpreter: Any, args: list[Any], line: int, col: int) -> Brack:
            if len(args) != 1:
                raise FlowRuntimeError("bk() takes exactly 1 argument", line=line, column=col, source_code=self.source_code)
            return parse_bk_input(args[0], line=line, col=col, source_code=self.source_code)

        self.globals.define("say", BuiltinFunction("say", builtin_say, expected_arity=None))
        self.globals.define("pow_", BuiltinFunction("pow_", builtin_pow, expected_arity=2))
        self.globals.define("input", BuiltinFunction("input", builtin_input, expected_arity=None))
        self.globals.define("int", BuiltinFunction("int", builtin_int, expected_arity=1))
        self.globals.define("flt", BuiltinFunction("flt", builtin_flt, expected_arity=1))
        self.globals.define("str", BuiltinFunction("str", builtin_str, expected_arity=1))
        self.globals.define("char", BuiltinFunction("char", builtin_char, expected_arity=1))
        self.globals.define("bool", BuiltinFunction("bool", builtin_bool, expected_arity=1))
        self.globals.define("len_", BuiltinFunction("len_", builtin_len, expected_arity=1))
        self.globals.define("append_", BuiltinFunction("append_", builtin_append, expected_arity=2))
        self.globals.define("remove_", BuiltinFunction("remove_", builtin_remove, expected_arity=2))
        self.globals.define("listb_", BuiltinFunction("listb_", builtin_listb, expected_arity=1))
        self.globals.define("freeze_", BuiltinFunction("freeze_", builtin_freeze, expected_arity=1))
        self.globals.define("bk", BuiltinFunction("bk", builtin_bk, expected_arity=1))

    # ------------------ Execution Entry Points ------------------

    def interpret(self, program: Program) -> Any:
        last_value = None
        for stmt in program.statements:
            last_value = self.execute(stmt)
        return last_value

    def execute(self, stmt: Statement) -> Any:
        if isinstance(stmt, ExpressionStatement):
            return self.evaluate(stmt.expression)

        if isinstance(stmt, VariableDeclaration):
            value = self.evaluate(stmt.initializer)
            self.environment.define(
                name=stmt.name,
                value=value,
                type_name=stmt.type_name,
                line=stmt.line,
                column=stmt.column,
                source_code=self.source_code,
            )
            return None

        if isinstance(stmt, Block):
            return self.execute_block(stmt.statements, Environment(parent=self.environment))

        if isinstance(stmt, IfStatement):
            condition = self.evaluate(stmt.condition)
            if self._is_truthy(condition):
                return self.execute(stmt.then_branch)
            elif stmt.else_branch is not None:
                return self.execute(stmt.else_branch)
            return None

        if isinstance(stmt, WhileStatement):
            last_value = None
            while self._is_truthy(self.evaluate(stmt.condition)):
                last_value = self.execute(stmt.body)
            return last_value

        if isinstance(stmt, DoWhileStatement):
            last_value = self.execute(stmt.body)
            while self._is_truthy(self.evaluate(stmt.condition)):
                last_value = self.execute(stmt.body)
            return last_value

        if isinstance(stmt, ForStatement):
            # Auto-declare loop variable in current environment
            init_val = self.evaluate(stmt.init_expr)
            self.environment.values[stmt.target] = init_val
            if stmt.target not in self.environment.types:
                self.environment.types[stmt.target] = "lit"

            last_val = None
            while self._is_truthy(self.evaluate(stmt.condition)):
                last_val = self.execute(stmt.body)
                self.evaluate(stmt.update)
            return last_val

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

            last_val = None
            for item in selected:
                self.environment.values[stmt.target] = make_independent_copy(item)
                if stmt.target not in self.environment.types:
                    self.environment.types[stmt.target] = "lit"
                last_val = self.execute(stmt.body)
            return last_val

        if isinstance(stmt, FunctionDeclaration):
            fn = UserFunction(
                name=stmt.name,
                parameters=stmt.parameters,
                body=stmt.body,
                closure=self.environment,
            )
            self.environment.define(stmt.name, fn, type_name="lit")
            return None

        if isinstance(stmt, ReturnStatement):
            val = self.evaluate(stmt.expression) if stmt.expression is not None else None
            raise ReturnSignal(val)

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
                if key in d:
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

            if isinstance(target, (FlowDict, dict)):
                validate_dict_key(index, expr.index.line, expr.index.column, self.source_code)
                if index not in target:
                    raise FlowRuntimeError(
                        f"KeyError: key {stringify_value(index)} not found in dictionary",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                return target[index]

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

            if isinstance(target, (Brack, tuple)):
                raise FlowRuntimeError(
                    "Cannot modify immutable brack: bracks do not support item assignment",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )

            if isinstance(target, (FlowDict, dict)):
                validate_dict_key(index, expr.index.line, expr.index.column, self.source_code)
                target[index] = value
                return value

            raise FlowRuntimeError(
                f"Type '{get_type_name(target)}' does not support index assignment",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if isinstance(expr, MemberAccess):
            target = self.evaluate(expr.target)
            member = expr.member
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
            value = self.evaluate(expr.value)
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
            return -operand

        if expr.operator == "not":
            return not self._is_truthy(operand)

        raise FlowRuntimeError(
            f"Unknown unary operator '{expr.operator}'",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_logical(self, expr: LogicalOp) -> Any:
        left = self.evaluate(expr.left)

        if expr.operator == "or":
            if self._is_truthy(left):
                return left
            return self.evaluate(expr.right)

        if expr.operator == "and":
            if not self._is_truthy(left):
                return left
            return self.evaluate(expr.right)

        raise FlowRuntimeError(
            f"Unknown logical operator '{expr.operator}'",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_binary(self, expr: BinaryOp) -> Any:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        op = expr.operator

        # Division: ALWAYS produces float in FlowLang V1
        if op == "/":
            self._check_number_operands(op, left, right, expr.line, expr.column)
            if right == 0:
                raise FlowRuntimeError(
                    "Division by zero",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return float(left / right)

        # Modulo
        if op == "%":
            self._check_number_operands(op, left, right, expr.line, expr.column)
            if right == 0:
                raise FlowRuntimeError(
                    "Modulo by zero",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return left % right

        # Subtraction
        if op == "-":
            self._check_number_operands(op, left, right, expr.line, expr.column)
            return left - right

        # Multiplication
        if op == "*":
            # Numbers
            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                return left * right

            # String * non-negative integer
            if isinstance(left, (str, Char)) and isinstance(right, int) and not isinstance(right, bool):
                if right < 0:
                    raise FlowRuntimeError(
                        "String multiplication requires a non-negative integer",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                text = left.value if isinstance(left, Char) else left
                return text * right

            # non-negative integer * String (symmetric)
            if isinstance(right, (str, Char)) and isinstance(left, int) and not isinstance(left, bool):
                if left < 0:
                    raise FlowRuntimeError(
                        "String multiplication requires a non-negative integer",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                text = right.value if isinstance(right, Char) else right
                return text * left

            raise FlowRuntimeError(
                f"Invalid operands for '*': '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        # Addition / Concatenation
        if op == "+":
            # Numbers
            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                return left + right

            # String concatenation (if either operand is string or char)
            if isinstance(left, (str, Char)) or isinstance(right, (str, Char)):
                s_left = left.value if isinstance(left, Char) else stringify_value(left)
                s_right = right.value if isinstance(right, Char) else stringify_value(right)
                return s_left + s_right

            raise FlowRuntimeError(
                f"Invalid operands for '+': '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        # Relational comparisons
        if op in (">", ">=", "<", "<="):
            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                if op == ">": return left > right
                if op == ">=": return left >= right
                if op == "<": return left < right
                if op == "<=": return left <= right

            if isinstance(left, (str, Char)) and isinstance(right, (str, Char)):
                s_left = left.value if isinstance(left, Char) else left
                s_right = right.value if isinstance(right, Char) else right
                if op == ">": return s_left > s_right
                if op == ">=": return s_left >= s_right
                if op == "<": return s_left < s_right
                if op == "<=": return s_left <= s_right

            raise FlowRuntimeError(
                f"Comparison operator '{op}' requires operands of same comparable type, got '{get_type_name(left)}' and '{get_type_name(right)}'",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        # Equality
        if op == "==":
            return left == right

        if op == "!=":
            return left != right

        raise FlowRuntimeError(
            f"Unknown binary operator '{op}'",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_call(self, expr: CallExpression) -> Any:
        callee = self.evaluate(expr.callee)

        if not isinstance(callee, FlowCallable):
            name = expr.callee.name if isinstance(expr.callee, Identifier) else str(callee)
            raise FlowRuntimeError(
                f"'{name}' is not callable",
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


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
    FunctionDeclaration,
    ReturnStatement,
    Assignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
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

        self.globals.define("say", BuiltinFunction("say", builtin_say, expected_arity=None))
        self.globals.define("pow_", BuiltinFunction("pow_", builtin_pow, expected_arity=2))
        self.globals.define("input", BuiltinFunction("input", builtin_input, expected_arity=None))
        self.globals.define("int", BuiltinFunction("int", builtin_int, expected_arity=1))
        self.globals.define("flt", BuiltinFunction("flt", builtin_flt, expected_arity=1))
        self.globals.define("str", BuiltinFunction("str", builtin_str, expected_arity=1))
        self.globals.define("char", BuiltinFunction("char", builtin_char, expected_arity=1))
        self.globals.define("bool", BuiltinFunction("bool", builtin_bool, expected_arity=1))

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


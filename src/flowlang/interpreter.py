"""FlowLang Tree-Walk Interpreter.

Walks the Abstract Syntax Tree (AST), executing statements and evaluating expressions.
Supports Python-like truthiness, short-circuit logical operators, for/while loops,
augmented assignments, and built-in functions (print, range, len, abs, type, int, float, str, bool).
"""

from typing import Any, Callable, Optional
from flowlang.ast import (
    ASTNode,
    Program,
    Statement,
    Expression,
    ExpressionStatement,
    VariableDeclaration,
    Block,
    IfStatement,
    WhileStatement,
    ForStatement,
    Assignment,
    AugmentedAssignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NoneLiteral,
    Identifier,
)
from flowlang.runtime import Environment, FlowCallable, BuiltinFunction, stringify_value
from flowlang.errors import FlowRuntimeError


class Interpreter:
    """Evaluates FlowLang AST nodes."""

    def __init__(
        self,
        globals_env: Optional[Environment] = None,
        output_handler: Optional[Callable[[str], None]] = None,
        source_code: Optional[str] = None,
    ):
        self.source_code = source_code
        self.output_handler = output_handler or print
        self.globals = globals_env if globals_env is not None else Environment()
        self.environment = self.globals
        self._init_builtins()

    def _init_builtins(self) -> None:
        """Register built-in functions in the global environment."""

        # print(*args) / say(*args)
        def builtin_print(interpreter: Any, args: list[Any], line: int, col: int) -> None:
            text = " ".join(stringify_value(arg) for arg in args)
            self.output_handler(text)
            return None

        # range(stop) | range(start, stop) | range(start, stop, step)
        def builtin_range(interpreter: Any, args: list[Any], line: int, col: int) -> list[int]:
            if not args or len(args) > 3:
                raise FlowRuntimeError(
                    f"range expected 1 to 3 arguments, got {len(args)}",
                    line=line, column=col, source_code=self.source_code
                )
            for a in args:
                if not isinstance(a, int) or isinstance(a, bool):
                    raise FlowRuntimeError(
                        f"range arguments must be integers, got {self._type_name(a)}",
                        line=line, column=col, source_code=self.source_code
                    )
            if len(args) == 1:
                return list(range(args[0]))
            elif len(args) == 2:
                return list(range(args[0], args[1]))
            else:
                if args[2] == 0:
                    raise FlowRuntimeError("range step must not be zero", line=line, column=col, source_code=self.source_code)
                return list(range(args[0], args[1], args[2]))

        # len(obj)
        def builtin_len(interpreter: Any, args: list[Any], line: int, col: int) -> int:
            if len(args) != 1:
                raise FlowRuntimeError(f"len() takes exactly one argument ({len(args)} given)", line=line, column=col, source_code=self.source_code)
            obj = args[0]
            if isinstance(obj, (str, list, tuple, dict)):
                return len(obj)
            raise FlowRuntimeError(f"object of type '{self._type_name(obj)}' has no len()", line=line, column=col, source_code=self.source_code)

        # abs(x)
        def builtin_abs(interpreter: Any, args: list[Any], line: int, col: int) -> Any:
            if len(args) != 1:
                raise FlowRuntimeError(f"abs() takes exactly one argument ({len(args)} given)", line=line, column=col, source_code=self.source_code)
            val = args[0]
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return abs(val)
            raise FlowRuntimeError(f"bad operand type for abs(): '{self._type_name(val)}'", line=line, column=col, source_code=self.source_code)

        # type(x)
        def builtin_type(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            if len(args) != 1:
                raise FlowRuntimeError(f"type() takes exactly one argument ({len(args)} given)", line=line, column=col, source_code=self.source_code)
            return self._type_name(args[0])

        # int(x)
        def builtin_int(interpreter: Any, args: list[Any], line: int, col: int) -> int:
            if len(args) != 1:
                raise FlowRuntimeError("int() takes exactly one argument", line=line, column=col, source_code=self.source_code)
            try:
                if isinstance(args[0], bool):
                    return 1 if args[0] else 0
                return int(args[0])
            except (ValueError, TypeError):
                raise FlowRuntimeError(f"invalid literal for int(): {args[0]!r}", line=line, column=col, source_code=self.source_code)

        # float(x)
        def builtin_float(interpreter: Any, args: list[Any], line: int, col: int) -> float:
            if len(args) != 1:
                raise FlowRuntimeError("float() takes exactly one argument", line=line, column=col, source_code=self.source_code)
            try:
                return float(args[0])
            except (ValueError, TypeError):
                raise FlowRuntimeError(f"could not convert string to float: {args[0]!r}", line=line, column=col, source_code=self.source_code)

        # str(x)
        def builtin_str(interpreter: Any, args: list[Any], line: int, col: int) -> str:
            if len(args) != 1:
                raise FlowRuntimeError("str() takes exactly one argument", line=line, column=col, source_code=self.source_code)
            return stringify_value(args[0])

        # bool(x)
        def builtin_bool(interpreter: Any, args: list[Any], line: int, col: int) -> bool:
            if len(args) != 1:
                raise FlowRuntimeError("bool() takes exactly one argument", line=line, column=col, source_code=self.source_code)
            return self._is_truthy(args[0])

        self.globals.define("print", BuiltinFunction("print", builtin_print, expected_arity=None))
        self.globals.define("say", BuiltinFunction("say", builtin_print, expected_arity=None))
        self.globals.define("range", BuiltinFunction("range", builtin_range, expected_arity=None))
        self.globals.define("len", BuiltinFunction("len", builtin_len, expected_arity=1))
        self.globals.define("abs", BuiltinFunction("abs", builtin_abs, expected_arity=1))
        self.globals.define("type", BuiltinFunction("type", builtin_type, expected_arity=1))
        self.globals.define("int", BuiltinFunction("int", builtin_int, expected_arity=1))
        self.globals.define("float", BuiltinFunction("float", builtin_float, expected_arity=1))
        self.globals.define("str", BuiltinFunction("str", builtin_str, expected_arity=1))
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
            self.environment.set(stmt.name, value)
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

        if isinstance(stmt, ForStatement):
            iterable = self.evaluate(stmt.iterable)
            if not hasattr(iterable, "__iter__") or isinstance(iterable, (bool, int, float)) or iterable is None:
                raise FlowRuntimeError(
                    f"'{self._type_name(iterable)}' object is not iterable",
                    line=stmt.line,
                    column=stmt.column,
                    source_code=self.source_code,
                )
            last_val = None
            for item in iterable:
                self.environment.set(stmt.target, item)
                last_val = self.execute(stmt.body)
            return last_val

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

        if isinstance(expr, BooleanLiteral):
            return expr.value

        if isinstance(expr, NoneLiteral):
            return None

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

        if isinstance(expr, AugmentedAssignment):
            return self._evaluate_augmented_assignment(expr)

        if isinstance(expr, CallExpression):
            return self._evaluate_call(expr)

        raise FlowRuntimeError(
            f"Unknown expression type: {type(expr).__name__}",
            line=expr.line,
            column=expr.column,
            source_code=self.source_code,
        )

    def _evaluate_augmented_assignment(self, expr: AugmentedAssignment) -> Any:
        current = self.environment.get(expr.name, expr.line, expr.column, self.source_code)
        val = self.evaluate(expr.value)
        op = expr.operator

        if op == "+=":
            if isinstance(current, (int, float)) and not isinstance(current, bool) and \
               isinstance(val, (int, float)) and not isinstance(val, bool):
                new_val = current + val
            elif isinstance(current, str) and isinstance(val, str):
                new_val = current + val
            else:
                raise FlowRuntimeError(
                    f"Unsupported operand types for +=: '{self._type_name(current)}' and '{self._type_name(val)}'",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
        elif op in ("-=", "*=", "/="):
            self._check_number_operands(op, current, val, expr.line, expr.column)
            if op == "-=":
                new_val = current - val
            elif op == "*=":
                new_val = current * val
            elif op == "/=":
                if val == 0:
                    raise FlowRuntimeError(
                        "Division by zero",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                res = current / val
                new_val = int(res) if res.is_integer() and isinstance(current, int) and isinstance(val, int) else res
        else:
            raise FlowRuntimeError(f"Unknown augmented assignment operator '{op}'", line=expr.line, column=expr.column, source_code=self.source_code)

        self.environment.assign(expr.name, new_val, expr.line, expr.column, self.source_code)
        return new_val

    def _evaluate_unary(self, expr: UnaryOp) -> Any:
        operand = self.evaluate(expr.operand)

        if expr.operator == "-":
            if not isinstance(operand, (int, float)) or isinstance(operand, bool):
                raise FlowRuntimeError(
                    f"Operand for unary '-' must be a number, got {self._type_name(operand)}",
                    line=expr.line,
                    column=expr.column,
                    source_code=self.source_code,
                )
            return -operand

        if expr.operator in ("!", "not"):
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

        if op == "+":
            if isinstance(left, (int, float)) and not isinstance(left, bool) and \
               isinstance(right, (int, float)) and not isinstance(right, bool):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise FlowRuntimeError(
                f"Operands for '+' must both be numbers or both be strings, got {self._type_name(left)} and {self._type_name(right)}",
                line=expr.line,
                column=expr.column,
                source_code=self.source_code,
            )

        if op in ("-", "*", "/", "%"):
            self._check_number_operands(op, left, right, expr.line, expr.column)
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise FlowRuntimeError(
                        "Division by zero",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                res = left / right
                return int(res) if res.is_integer() and isinstance(left, int) and isinstance(right, int) else res
            if op == "%":
                if right == 0:
                    raise FlowRuntimeError(
                        "Modulo by zero",
                        line=expr.line,
                        column=expr.column,
                        source_code=self.source_code,
                    )
                return left % right

        if op in (">", ">=", "<", "<="):
            self._check_number_operands(op, left, right, expr.line, expr.column)
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right

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
        if isinstance(value, (list, tuple, dict)):
            return len(value) > 0
        return True

    def _check_number_operands(self, operator: str, left: Any, right: Any, line: int, column: int) -> None:
        left_is_num = isinstance(left, (int, float)) and not isinstance(left, bool)
        right_is_num = isinstance(right, (int, float)) and not isinstance(right, bool)
        if not (left_is_num and right_is_num):
            raise FlowRuntimeError(
                f"Operands for '{operator}' must be numbers, got {self._type_name(left)} and {self._type_name(right)}",
                line=line,
                column=column,
                source_code=self.source_code,
            )

    @staticmethod
    def _type_name(val: Any) -> str:
        if val is None:
            return "None"
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        if isinstance(val, str):
            return "str"
        if isinstance(val, list):
            return "list"
        return type(val).__name__

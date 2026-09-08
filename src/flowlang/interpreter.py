"""FlowLang Tree-Walk Interpreter.

Walks the Abstract Syntax Tree (AST), executing statements and evaluating expressions.
Supports Python-like truthiness, short-circuit logical operators, and built-in print.
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
    Assignment,
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
        def builtin_print(interpreter: Any, args: list[Any], line: int, col: int) -> None:
            text = " ".join(stringify_value(arg) for arg in args)
            self.output_handler(text)
            return None

        # Register both 'print' (Python style) and 'say'
        self.globals.define("print", BuiltinFunction("print", builtin_print, expected_arity=None))
        self.globals.define("say", BuiltinFunction("say", builtin_print, expected_arity=None))

    # ------------------ Execution Entry Points ------------------

    def interpret(self, program: Program) -> Any:
        """Execute a full Program AST and return the value of the last evaluated expression statement."""
        last_value = None
        for stmt in program.statements:
            last_value = self.execute(stmt)
        return last_value

    def execute(self, stmt: Statement) -> Any:
        """Execute a single statement."""
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

        raise FlowRuntimeError(
            f"Unknown statement type: {type(stmt).__name__}",
            line=stmt.line,
            column=stmt.column,
            source_code=self.source_code,
        )

    def execute_block(self, statements: list[Statement], block_env: Environment) -> Any:
        """Execute a series of statements in an isolated scope."""
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
        """Evaluate an expression AST node and return its runtime value."""
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
        """Evaluate short-circuiting logical AND / OR operators."""
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

        # Arithmetic operators
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

        # Comparison operators
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

        # Equality operators
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
        """Python-style truthiness: False, None, 0, and empty string are falsey."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
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
        return type(val).__name__

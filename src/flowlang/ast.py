"""FlowLang Abstract Syntax Tree (AST) definitions.

AST nodes represent the syntactic structure of FlowLang programs.
Nodes are purely structural data containers with line/column tracking,
independent of interpreter execution logic.
"""

from dataclasses import dataclass
from typing import Optional, Union, Any


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int
    column: int


# ==================== Expressions ====================

@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""
    pass


@dataclass
class NumberLiteral(Expression):
    value: Union[int, float]

    def __repr__(self) -> str:
        return f"Number({self.value})"


@dataclass
class StringLiteral(Expression):
    value: str

    def __repr__(self) -> str:
        return f"String({self.value!r})"


@dataclass
class BooleanLiteral(Expression):
    value: bool

    def __repr__(self) -> str:
        return f"Bool({self.value})"


@dataclass
class Identifier(Expression):
    name: str

    def __repr__(self) -> str:
        return f"Ident({self.name})"


@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression

    def __repr__(self) -> str:
        return f"Binary({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

    def __repr__(self) -> str:
        return f"Unary({self.operator}{self.operand})"


@dataclass
class Grouping(Expression):
    expression: Expression

    def __repr__(self) -> str:
        return f"Grouping({self.expression})"


@dataclass
class Assignment(Expression):
    name: str
    value: Expression

    def __repr__(self) -> str:
        return f"Assign({self.name} = {self.value})"


@dataclass
class CallExpression(Expression):
    callee: Expression
    arguments: list[Expression]

    def __repr__(self) -> str:
        args = ", ".join(repr(a) for a in self.arguments)
        return f"Call({self.callee}({args}))"


# ==================== Statements ====================

@dataclass
class Statement(ASTNode):
    """Base class for all statements."""
    pass


@dataclass
class ExpressionStatement(Statement):
    expression: Expression

    def __repr__(self) -> str:
        return f"ExprStmt({self.expression})"


@dataclass
class VariableDeclaration(Statement):
    name: str
    initializer: Expression

    def __repr__(self) -> str:
        return f"Let({self.name} = {self.initializer})"


@dataclass
class Block(Statement):
    statements: list[Statement]

    def __repr__(self) -> str:
        return f"Block({self.statements})"


@dataclass
class IfStatement(Statement):
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement] = None

    def __repr__(self) -> str:
        if self.else_branch:
            return f"If({self.condition}, then={self.then_branch}, else={self.else_branch})"
        return f"If({self.condition}, then={self.then_branch})"


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Statement

    def __repr__(self) -> str:
        return f"While({self.condition}, body={self.body})"


@dataclass
class Program(ASTNode):
    statements: list[Statement]

    def __repr__(self) -> str:
        return f"Program({self.statements})"

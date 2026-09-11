"""FlowLang Abstract Syntax Tree (AST) definitions.

AST nodes represent the syntactic structure of FlowLang V1 programs.
Nodes are purely structural data containers with line/column tracking.
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
class CharLiteral(Expression):
    value: str

    def __repr__(self) -> str:
        return f"Char({self.value!r})"


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
class LogicalOp(Expression):
    left: Expression
    operator: str  # "and" | "or"
    right: Expression

    def __repr__(self) -> str:
        return f"Logical({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

    def __repr__(self) -> str:
        return f"Unary({self.operator} {self.operand})"


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


@dataclass
class ListLiteral(Expression):
    elements: list[Expression]

    def __repr__(self) -> str:
        elems = ", ".join(repr(e) for e in self.elements)
        return f"List([{elems}])"


@dataclass
class BrackLiteral(Expression):
    elements: list[Expression]

    def __repr__(self) -> str:
        elems = ", ".join(repr(e) for e in self.elements)
        return f"Brack(({elems}))"


@dataclass
class DictLiteral(Expression):
    entries: list[tuple[Expression, Expression]]

    def __repr__(self) -> str:
        items = ", ".join(f"{k}: {v}" for k, v in self.entries)
        return f"Dict(<< {items} >>)"


@dataclass
class IndexAccess(Expression):
    target: Expression
    index: Expression

    def __repr__(self) -> str:
        return f"IndexAccess({self.target}[{self.index}])"


@dataclass
class IndexAssignment(Expression):
    target: Expression
    index: Expression
    value: Expression

    def __repr__(self) -> str:
        return f"IndexAssign({self.target}[{self.index}] = {self.value})"


@dataclass
class MemberAccess(Expression):
    target: Expression
    member: str

    def __repr__(self) -> str:
        return f"MemberAccess({self.target}.{self.member})"


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
    type_name: str  # "lit", "int", "flt", "str", "char", "bool"
    name: str
    initializer: Expression

    def __repr__(self) -> str:
        return f"VarDecl({self.type_name} {self.name} = {self.initializer})"


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
class DoWhileStatement(Statement):
    body: Statement
    condition: Expression

    def __repr__(self) -> str:
        return f"DoWhile(body={self.body}, cond={self.condition})"


@dataclass
class ForStatement(Statement):
    target: str
    init_expr: Expression
    condition: Expression
    update: Expression
    body: Statement

    def __repr__(self) -> str:
        return f"For({self.target} in ({self.init_expr}; {self.condition}; {self.update}), body={self.body})"


@dataclass
class ForInStatement(Statement):
    target: str
    iterable: Expression
    range_args: Optional[list[Expression]]
    body: Statement

    def __repr__(self) -> str:
        if self.range_args is not None:
            r = "; ".join(repr(a) for a in self.range_args)
            return f"ForIn({self.target} in {self.iterable}({r}), body={self.body})"
        return f"ForIn({self.target} in {self.iterable}, body={self.body})"


@dataclass
class FunctionDeclaration(Statement):
    name: str
    parameters: list[str]
    body: Block

    def __repr__(self) -> str:
        params = ", ".join(self.parameters)
        return f"Dfn({self.name}({params}), body={self.body})"


@dataclass
class ReturnStatement(Statement):
    expression: Optional[Expression] = None

    def __repr__(self) -> str:
        return f"Return({self.expression})"


@dataclass
class ImportStatement(Statement):
    module_name: str

    def __repr__(self) -> str:
        return f"Import({self.module_name})"


@dataclass
class Program(ASTNode):
    statements: list[Statement]

    def __repr__(self) -> str:
        return f"Program({self.statements})"

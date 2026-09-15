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


@dataclass
class CompoundAssignment(Expression):
    target: Expression
    operator: str  # "+=", "-=", "*=", "//=", "%="
    value: Expression

    def __repr__(self) -> str:
        return f"CompoundAssign({self.target} {self.operator} {self.value})"


@dataclass
class StructLiteral(Expression):
    struct_name: str
    values: list[Expression]

    def __repr__(self) -> str:
        vals = ", ".join(repr(v) for v in self.values)
        return f"StructLit({self.struct_name} << {vals} >>)"


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
    type_name: str  # "lit", "int", "flt", "str", "char", "bool", or custom struct name
    name: str
    initializer: Expression
    is_mutable: bool = False

    def __repr__(self) -> str:
        mut_prefix = "mut " if self.is_mutable else ""
        return f"VarDecl({mut_prefix}{self.type_name} {self.name} = {self.initializer})"


@dataclass
class BreakStatement(Statement):
    def __repr__(self) -> str:
        return "Break()"


@dataclass
class ContinueStatement(Statement):
    def __repr__(self) -> str:
        return "Continue()"


@dataclass
class StructDeclaration(Statement):
    name: str
    fields: list[tuple[str, str]]  # list of (field_name, type_name)

    def __repr__(self) -> str:
        f = ", ".join(f"{t} {n}" for n, t in self.fields)
        return f"StructDecl({self.name} = << {f} >>)"


@dataclass
class EnumDeclaration(Statement):
    name: str
    members: list[str]  # list of member names

    def __repr__(self) -> str:
        m = ", ".join(self.members)
        return f"EnumDecl({self.name} = << {m} >>)"


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
    parameters: list[tuple[str, str]]
    return_type: str
    body: Block

    def __repr__(self) -> str:
        params = ", ".join(f"{t} {n}" for n, t in self.parameters)
        return f"Dfn({self.name}({params}) -> {self.return_type}, body={self.body})"


@dataclass
class ReturnStatement(Statement):
    expression: Optional[Expression] = None

    def __repr__(self) -> str:
        return f"Return({self.expression})"


@dataclass
class TryCatchStatement(Statement):
    try_block: Block
    error_type: str
    error_name: str
    catch_block: Block

    def __repr__(self) -> str:
        return f"TryCatch(try={self.try_block}, catch=({self.error_type} {self.error_name}) {self.catch_block})"


@dataclass
class RaiseStatement(Statement):
    expression: Expression

    def __repr__(self) -> str:
        return f"Raise({self.expression})"


@dataclass
class GlobalStatement(Statement):
    name: str

    def __repr__(self) -> str:
        return f"Global({self.name})"


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

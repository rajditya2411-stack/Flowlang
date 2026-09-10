"""FlowLang Token Definitions.

Defines all token types and the Token representation with source location tracking.
Supports FlowLang V1 syntax with brace blocks, typed/dynamic variable declarations,
loops, functions, logical operators, and literals.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Literals
    NUMBER = auto()         # Integer or Float numeric literal
    STRING = auto()         # Double-quoted string "..."
    CHAR = auto()           # Single-quoted character 'c'
    IDENTIFIER = auto()     # Identifier name

    # Boolean Literals
    TRUE = auto()           # true
    FALSE = auto()          # false

    # Type & Variable Declaration Keywords
    LIT = auto()            # lit
    INT = auto()            # int
    FLT = auto()            # flt
    STR = auto()            # str
    CHAR_TYPE = auto()      # char
    BOOL_TYPE = auto()      # bool

    # Control Flow Keywords
    IF = auto()             # if
    ELIF = auto()           # elif
    ELSE = auto()           # else
    WHILE = auto()          # while
    DO = auto()             # do
    FOR = auto()            # for
    IN = auto()             # in

    # Function & Return Keywords
    DFN = auto()            # dfn
    RETURN = auto()         # return

    # Output Keyword / Identifier
    SAY = auto()            # say

    # Logical Operators (word-based)
    AND = auto()            # and
    OR = auto()             # or
    NOT = auto()            # not

    # Arithmetic & Assignment Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    MODULO = auto()         # %
    ASSIGN = auto()         # =

    # Comparison Operators
    EQUAL = auto()          # ==
    NOT_EQUAL = auto()      # !=
    LESS = auto()           # <
    GREATER = auto()        # >
    LESS_EQUAL = auto()     # <=
    GREATER_EQUAL = auto()  # >=

    # Punctuation & Delimiters
    COMMA = auto()          # ,
    SEMICOLON = auto()      # ;
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }

    # Structural
    NEWLINE = auto()
    EOF = auto()


# Keyword lookup table for FlowLang V1 (all lowercase)
KEYWORDS: dict[str, TokenType] = {
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "lit": TokenType.LIT,
    "int": TokenType.INT,
    "flt": TokenType.FLT,
    "str": TokenType.STR,
    "char": TokenType.CHAR_TYPE,
    "bool": TokenType.BOOL_TYPE,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "dfn": TokenType.DFN,
    "return": TokenType.RETURN,
    "say": TokenType.SAY,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


@dataclass(frozen=True)
class Token:
    """Represents a lexical token with its position in source code."""
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        if self.value is not None:
            return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
        return f"Token({self.type.name}, line={self.line}, col={self.column})"

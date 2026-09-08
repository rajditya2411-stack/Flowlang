"""FlowLang Token Definitions.

Defines all token types and the Token representation with source location tracking.
Supports Python-like syntax including INDENT, DEDENT, colons, and logical keywords.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords & Literals
    TRUE = auto()
    FALSE = auto()
    NONE = auto()

    # Control Flow Keywords
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DEF = auto()
    RETURN = auto()
    LET = auto()            # Optional backwards-compatibility

    # Logical Operators
    AND = auto()
    OR = auto()
    NOT = auto()

    # Arithmetic & Comparison Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    MODULO = auto()         # %
    ASSIGN = auto()         # =
    EQUAL = auto()          # ==
    NOT_EQUAL = auto()      # !=
    LESS = auto()           # <
    GREATER = auto()        # >
    LESS_EQUAL = auto()     # <=
    GREATER_EQUAL = auto()  # >=
    BANG = auto()           # !

    # Punctuation & Delimiters
    COLON = auto()          # :
    COMMA = auto()          # ,
    DOT = auto()            # .
    SEMICOLON = auto()      # ;
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    LBRACE = auto()         # {
    RBRACE = auto()         # }

    # Indentation & Structural
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


# Keyword lookup table (Python-style keywords + ergonomic fallbacks)
KEYWORDS: dict[str, TokenType] = {
    # Python style
    "True": TokenType.TRUE,
    "False": TokenType.FALSE,
    "None": TokenType.NONE,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "def": TokenType.DEF,
    "return": TokenType.RETURN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,

    # Fallbacks / aliases
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "none": TokenType.NONE,
    "nil": TokenType.NONE,
    "fn": TokenType.DEF,
    "let": TokenType.LET,
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

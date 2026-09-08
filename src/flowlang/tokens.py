"""FlowLang Token Definitions.

Defines all token types and the Token representation with source location tracking.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FN = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()

    # Operators
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

    # Punctuation
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    COMMA = auto()          # ,
    DOT = auto()            # .
    COLON = auto()          # :
    SEMICOLON = auto()      # ;

    # Structural
    NEWLINE = auto()
    EOF = auto()


# Keyword lookup table: easily extensible for new keywords
KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
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

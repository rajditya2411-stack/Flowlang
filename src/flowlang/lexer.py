"""FlowLang Lexer.

Converts raw source code into a stream of Token objects.
Tracks line and column numbers accurately for friendly error reporting.
"""

from typing import Optional
from flowlang.tokens import Token, TokenType, KEYWORDS
from flowlang.errors import LexerError


class Lexer:
    """Lexical analyzer for FlowLang."""

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        """Look ahead without consuming."""
        target = self.pos + offset
        if target < self.length:
            return self.source[target]
        return None

    def _advance(self) -> Optional[str]:
        """Consume and return the current character, updating line and column."""
        if self.pos >= self.length:
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        """Consume next character only if it matches expected."""
        if self.pos >= self.length or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def tokenize(self) -> list[Token]:
        """Tokenize the entire source string into a list of Tokens ending with EOF."""
        tokens: list[Token] = []

        while self.pos < self.length:
            char = self._peek()

            # Whitespace (spaces, tabs, carriage returns)
            if char in (" ", "\t", "\r"):
                self._advance()
                continue

            # Newlines
            if char == "\n":
                start_line = self.line
                start_col = self.column
                self._advance()
                # Emit NEWLINE token, collapsing consecutive newlines
                if tokens and tokens[-1].type != TokenType.NEWLINE:
                    tokens.append(Token(TokenType.NEWLINE, "\n", start_line, start_col))
                continue

            # Comments: // ...
            if char == "/" and self._peek(1) == "/":
                self._advance()  # consume first /
                self._advance()  # consume second /
                while self._peek() is not None and self._peek() != "\n":
                    self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # Numbers: integers and floats
            if char.isdigit():
                tokens.append(self._lex_number(start_line, start_col))
                continue

            # Strings: "..."
            if char == '"':
                tokens.append(self._lex_string(start_line, start_col))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == "_":
                tokens.append(self._lex_identifier(start_line, start_col))
                continue

            # Two-character or single-character operators
            if char == "=":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.EQUAL, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
                continue

            if char == "!":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.NOT_EQUAL, "!=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.BANG, "!", start_line, start_col))
                continue

            if char == "<":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.LESS_EQUAL, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LESS, "<", start_line, start_col))
                continue

            if char == ">":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.GREATER_EQUAL, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GREATER, ">", start_line, start_col))
                continue

            # Single-character operators and punctuation
            simple_tokens = {
                "+": (TokenType.PLUS, "+"),
                "-": (TokenType.MINUS, "-"),
                "*": (TokenType.STAR, "*"),
                "/": (TokenType.SLASH, "/"),
                "%": (TokenType.MODULO, "%"),
                "(": (TokenType.LPAREN, "("),
                ")": (TokenType.RPAREN, ")"),
                "{": (TokenType.LBRACE, "{"),
                "}": (TokenType.RBRACE, "}"),
                "[": (TokenType.LBRACKET, "["),
                "]": (TokenType.RBRACKET, "]"),
                ",": (TokenType.COMMA, ","),
                ".": (TokenType.DOT, "."),
                ":": (TokenType.COLON, ":"),
                ";": (TokenType.SEMICOLON, ";"),
            }

            if char in simple_tokens:
                token_type, value = simple_tokens[char]
                self._advance()
                tokens.append(Token(token_type, value, start_line, start_col))
                continue

            # If we reach here, it is an unrecognized character
            self._advance()
            raise LexerError(
                f"Unexpected character '{char}'",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        # Remove trailing NEWLINE before EOF if present
        if tokens and tokens[-1].type == TokenType.NEWLINE:
            tokens.pop()

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def _lex_number(self, start_line: int, start_col: int) -> Token:
        """Lex integer or decimal number."""
        num_str = ""
        has_dot = False

        while self._peek() is not None:
            c = self._peek()
            if c.isdigit():
                num_str += self._advance()
            elif c == "." and not has_dot:
                # Lookahead: is the next character a digit?
                # If so, it's a decimal number like 3.14. If not (e.g. 3.method()), dot is separate.
                next_c = self._peek(1)
                if next_c is not None and next_c.isdigit():
                    has_dot = True
                    num_str += self._advance()  # consume '.'
                else:
                    break
            elif c == "." and has_dot:
                # Extra dot in number, e.g. 1.2.3 -> Malformed number
                dot_line, dot_col = self.line, self.column
                self._advance()
                raise LexerError(
                    f"Malformed number '{num_str}.'",
                    line=dot_line,
                    column=dot_col,
                    source_code=self.source,
                )
            else:
                break

        if has_dot:
            return Token(TokenType.NUMBER, float(num_str), start_line, start_col)
        return Token(TokenType.NUMBER, int(num_str), start_line, start_col)

    def _lex_string(self, start_line: int, start_col: int) -> Token:
        """Lex double-quoted string with escape characters."""
        self._advance()  # Consume opening '"'
        result = ""

        while True:
            char = self._peek()
            if char is None or char == "\n":
                raise LexerError(
                    "Unterminated string literal",
                    line=start_line,
                    column=start_col,
                    source_code=self.source,
                )

            if char == '"':
                self._advance()  # Consume closing '"'
                break

            if char == "\\":
                self._advance()  # Consume '\'
                escape = self._peek()
                if escape is None:
                    raise LexerError(
                        "Unterminated escape sequence in string",
                        line=start_line,
                        column=start_col,
                        source_code=self.source,
                    )
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    '"': '"',
                    "\\": "\\",
                }
                if escape in escape_map:
                    result += escape_map[escape]
                    self._advance()
                else:
                    # Keep raw or error? In FlowLang, raise error on invalid escape
                    escape_col = self.column
                    self._advance()
                    raise LexerError(
                        f"Unknown escape sequence '\\{escape}'",
                        line=self.line,
                        column=escape_col,
                        source_code=self.source,
                    )
            else:
                result += self._advance()

        return Token(TokenType.STRING, result, start_line, start_col)

    def _lex_identifier(self, start_line: int, start_col: int) -> Token:
        """Lex identifier or keyword."""
        name = ""
        while self._peek() is not None and (self._peek().isalnum() or self._peek() == "_"):
            name += self._advance()

        # Check if it's a keyword
        if name in KEYWORDS:
            token_type = KEYWORDS[name]
            if token_type == TokenType.TRUE:
                return Token(TokenType.TRUE, True, start_line, start_col)
            elif token_type == TokenType.FALSE:
                return Token(TokenType.FALSE, False, start_line, start_col)
            return Token(token_type, name, start_line, start_col)

        return Token(TokenType.IDENTIFIER, name, start_line, start_col)

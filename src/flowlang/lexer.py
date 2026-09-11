"""FlowLang Lexer.

Converts raw FlowLang V1 source code into a stream of Token objects.
Tracks line/column positions accurately for friendly error reporting.
Supports C-style block comments (/* ... */), single-line comments (# ...),
character literals ('c'), string literals ("..."), braces, and keywords.
"""

from typing import Optional
from flowlang.tokens import Token, TokenType, KEYWORDS
from flowlang.errors import LexerError


class Lexer:
    """Lexical analyzer for FlowLang V1."""

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        target = self.pos + offset
        if target < self.length:
            return self.source[target]
        return None

    def _advance(self) -> Optional[str]:
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
        if self.pos >= self.length or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        while self.pos < self.length:
            char = self._peek()
            if char is None:
                break

            # Whitespace within lines
            if char in (" ", "\t", "\r"):
                self._advance()
                continue

            # Newlines
            if char == "\n":
                start_line = self.line
                start_col = self.column
                self._advance()
                if tokens and tokens[-1].type != TokenType.NEWLINE:
                    tokens.append(Token(TokenType.NEWLINE, "\n", start_line, start_col))
                continue

            start_line = self.line
            start_col = self.column

            # Block comments: /* ... */
            if char == "/" and self._peek(1) == "*":
                self._advance()  # '/'
                self._advance()  # '*'
                comment_closed = False
                while self.pos < self.length:
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()  # '*'
                        self._advance()  # '/'
                        comment_closed = True
                        break
                    self._advance()
                if not comment_closed:
                    raise LexerError(
                        "Unterminated block comment '/*'",
                        line=start_line,
                        column=start_col,
                        source_code=self.source,
                    )
                continue

            # Single-line comments: '#' or '//'
            if char == "#" or (char == "/" and self._peek(1) == "/"):
                while self._peek() is not None and self._peek() != "\n":
                    self._advance()
                continue

            # Numbers: integers and floats
            if char.isdigit():
                tokens.append(self._lex_number(start_line, start_col))
                continue

            # Double-quoted Strings: "..."
            if char == '"':
                tokens.append(self._lex_string(start_line, start_col))
                continue

            # Single-quoted Characters: 'c'
            if char == "'":
                tokens.append(self._lex_char(start_line, start_col))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == "_":
                tokens.append(self._lex_identifier(start_line, start_col))
                continue

            # Operators
            if char == "+":
                self._advance()
                tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
                continue

            if char == "-":
                self._advance()
                tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
                continue

            if char == "*":
                self._advance()
                tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
                continue

            if char == "/":
                self._advance()
                tokens.append(Token(TokenType.SLASH, "/", start_line, start_col))
                continue

            if char == "%":
                self._advance()
                tokens.append(Token(TokenType.MODULO, "%", start_line, start_col))
                continue

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
                    raise LexerError(
                        "Unexpected character '!' (use 'not' for logical negation or '!=' for inequality)",
                        line=start_line,
                        column=start_col,
                        source_code=self.source,
                    )
                continue

            if char == "<":
                self._advance()
                if self._match("<"):
                    tokens.append(Token(TokenType.LDICT, "<<", start_line, start_col))
                elif self._match("="):
                    tokens.append(Token(TokenType.LESS_EQUAL, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LESS, "<", start_line, start_col))
                continue

            if char == ">":
                self._advance()
                if self._match(">"):
                    tokens.append(Token(TokenType.RDICT, ">>", start_line, start_col))
                elif self._match("="):
                    tokens.append(Token(TokenType.GREATER_EQUAL, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GREATER, ">", start_line, start_col))
                continue

            # Delimiters and Punctuation
            delims = {
                "(": (TokenType.LPAREN, "("),
                ")": (TokenType.RPAREN, ")"),
                "{": (TokenType.LBRACE, "{"),
                "}": (TokenType.RBRACE, "}"),
                "[": (TokenType.LBRACKET, "["),
                "]": (TokenType.RBRACKET, "]"),
                ",": (TokenType.COMMA, ","),
                ";": (TokenType.SEMICOLON, ";"),
                ":": (TokenType.COLON, ":"),
                ".": (TokenType.DOT, "."),
            }

            if char in delims:
                token_type, val = delims[char]
                self._advance()
                tokens.append(Token(token_type, val, start_line, start_col))
                continue

            # Unrecognized character
            self._advance()
            raise LexerError(
                f"Unexpected character '{char}'",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def _lex_number(self, start_line: int, start_col: int) -> Token:
        num_str = ""
        has_dot = False

        while self._peek() is not None:
            c = self._peek()
            if c.isdigit():
                num_str += self._advance()
            elif c == "." and not has_dot:
                next_c = self._peek(1)
                if next_c is not None and next_c.isdigit():
                    has_dot = True
                    num_str += self._advance()
                else:
                    break
            elif c == "." and has_dot:
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
        self._advance()  # opening "
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
                self._advance()  # closing "
                break

            if char == "\\":
                self._advance()
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
                    "'": "'",
                    "\\": "\\",
                }
                if escape in escape_map:
                    result += escape_map[escape]
                    self._advance()
                else:
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

    def _lex_char(self, start_line: int, start_col: int) -> Token:
        self._advance()  # opening '
        char_val = ""

        if self._peek() is None or self._peek() == "\n":
            raise LexerError(
                "Unterminated character literal",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        if self._peek() == "'":
            self._advance()
            raise LexerError(
                "Empty character literal ''",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        if self._peek() == "\\":
            self._advance()
            escape = self._peek()
            if escape is None:
                raise LexerError(
                    "Unterminated escape sequence in character literal",
                    line=start_line,
                    column=start_col,
                    source_code=self.source,
                )
            escape_map = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                '"': '"',
                "'": "'",
                "\\": "\\",
                "0": "\0",
            }
            if escape in escape_map:
                char_val = escape_map[escape]
                self._advance()
            else:
                escape_col = self.column
                self._advance()
                raise LexerError(
                    f"Unknown escape sequence '\\{escape}'",
                    line=self.line,
                    column=escape_col,
                    source_code=self.source,
                )
        else:
            char_val = self._advance()

        if self._peek() != "'":
            raise LexerError(
                "Multi-character character literal (use double quotes for strings)",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        self._advance()  # closing '
        return Token(TokenType.CHAR, char_val, start_line, start_col)

    def _lex_identifier(self, start_line: int, start_col: int) -> Token:
        name = ""
        while self._peek() is not None and (self._peek().isalnum() or self._peek() == "_"):
            name += self._advance()

        if name in KEYWORDS:
            token_type = KEYWORDS[name]
            if token_type == TokenType.TRUE:
                return Token(TokenType.TRUE, True, start_line, start_col)
            elif token_type == TokenType.FALSE:
                return Token(TokenType.FALSE, False, start_line, start_col)
            return Token(token_type, name, start_line, start_col)

        return Token(TokenType.IDENTIFIER, name, start_line, start_col)

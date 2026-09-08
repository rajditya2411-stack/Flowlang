"""FlowLang Lexer.

Converts raw source code into a stream of Token objects.
Implements Python-style indentation tracking (INDENT, DEDENT, NEWLINE)
and tracks line/column positions accurately for friendly error reporting.
"""

from typing import Optional
from flowlang.tokens import Token, TokenType, KEYWORDS
from flowlang.errors import LexerError


class Lexer:
    """Lexical analyzer for FlowLang with Python-like indentation support."""

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.paren_level = 0
        self.indent_stack = [0]
        self.at_line_start = True

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
            if self.at_line_start:
                self.at_line_start = False
                indent_tokens = self._handle_indentation()
                tokens.extend(indent_tokens)
                if self.pos >= self.length:
                    break

            char = self._peek()
            if char is None:
                break

            # Spaces and tabs within a line
            if char in (" ", "\t", "\r"):
                self._advance()
                continue

            # Newlines
            if char == "\n":
                start_line = self.line
                start_col = self.column
                self._advance()
                self.at_line_start = True
                if self.paren_level == 0:
                    if tokens and tokens[-1].type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                        tokens.append(Token(TokenType.NEWLINE, "\n", start_line, start_col))
                continue

            # Comments: '#' (Python style) or '//'
            if char == "#" or (char == "/" and self._peek(1) == "/"):
                while self._peek() is not None and self._peek() != "\n":
                    self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # Numbers: integers and floats
            if char.isdigit():
                tokens.append(self._lex_number(start_line, start_col))
                continue

            # Strings: "..." or '...'
            if char in ('"', "'"):
                tokens.append(self._lex_string(start_line, start_col, quote_char=char))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == "_":
                tokens.append(self._lex_identifier(start_line, start_col))
                continue

            # Track parentheses / brackets depth
            if char in ("(", "[", "{"):
                self.paren_level += 1
            elif char in (")", "]", "}"):
                if self.paren_level > 0:
                    self.paren_level -= 1

            # Two-character or single-character operators
            if char == "+":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
                continue

            if char == "-":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
                continue

            if char == "*":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.STAR_ASSIGN, "*=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
                continue

            if char == "/":
                self._advance()
                if self._match("="):
                    tokens.append(Token(TokenType.SLASH_ASSIGN, "/=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.SLASH, "/", start_line, start_col))
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
                "%": (TokenType.MODULO, "%"),
                ":": (TokenType.COLON, ":"),
                "(": (TokenType.LPAREN, "("),
                ")": (TokenType.RPAREN, ")"),
                "{": (TokenType.LBRACE, "{"),
                "}": (TokenType.RBRACE, "}"),
                "[": (TokenType.LBRACKET, "["),
                "]": (TokenType.RBRACKET, "]"),
                ",": (TokenType.COMMA, ","),
                ".": (TokenType.DOT, "."),
                ";": (TokenType.SEMICOLON, ";"),
            }

            if char in simple_tokens:
                token_type, value = simple_tokens[char]
                self._advance()
                tokens.append(Token(token_type, value, start_line, start_col))
                continue

            # Unrecognized character
            self._advance()
            raise LexerError(
                f"Unexpected character '{char}'",
                line=start_line,
                column=start_col,
                source_code=self.source,
            )

        # End of source cleanup: emit final NEWLINE and DEDENTs
        if self.paren_level == 0 and tokens and tokens[-1].type not in (TokenType.NEWLINE, TokenType.DEDENT):
            tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, None, self.line, self.column))

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def _handle_indentation(self) -> list[Token]:
        tokens: list[Token] = []

        while self.pos < self.length:
            indent = 0
            start_line = self.line
            start_col = self.column

            while self.pos < self.length:
                c = self.source[self.pos]
                if c == " ":
                    indent += 1
                    self._advance()
                elif c == "\t":
                    indent += 4
                    self._advance()
                else:
                    break

            if self.pos < self.length:
                c = self.source[self.pos]
                if c == "\n":
                    self._advance()
                    continue
                if c == "#" or (c == "/" and self._peek(1) == "/"):
                    while self._peek() is not None and self._peek() != "\n":
                        self._advance()
                    if self._peek() == "\n":
                        self._advance()
                    continue

            if self.pos >= self.length:
                break

            if self.paren_level > 0:
                break

            current_indent = self.indent_stack[-1]
            if indent > current_indent:
                self.indent_stack.append(indent)
                tokens.append(Token(TokenType.INDENT, indent, start_line, start_col))
            elif indent < current_indent:
                while self.indent_stack[-1] > indent:
                    self.indent_stack.pop()
                    tokens.append(Token(TokenType.DEDENT, None, start_line, start_col))
                if self.indent_stack[-1] != indent:
                    raise LexerError(
                        "Unindent does not match any outer indentation level",
                        line=start_line,
                        column=start_col,
                        source_code=self.source,
                    )
            break

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

    def _lex_string(self, start_line: int, start_col: int, quote_char: str = '"') -> Token:
        self._advance()
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

            if char == quote_char:
                self._advance()
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
            elif token_type == TokenType.NONE:
                return Token(TokenType.NONE, None, start_line, start_col)
            return Token(token_type, name, start_line, start_col)

        return Token(TokenType.IDENTIFIER, name, start_line, start_col)

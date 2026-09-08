"""FlowLang Recursive-Descent Parser.

Consumes a stream of tokens and constructs an Abstract Syntax Tree (AST).
Enforces correct operator precedence and provides rich syntax error messages.
"""

from typing import Optional, List
from flowlang.tokens import Token, TokenType
from flowlang.errors import ParserError
from flowlang.ast import (
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
    UnaryOp,
    Grouping,
    CallExpression,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    Identifier,
)


class Parser:
    """Recursive-descent parser for FlowLang."""

    def __init__(self, tokens: list[Token], source_code: Optional[str] = None):
        self.tokens = tokens
        self.source_code = source_code
        self.pos = 0

    # ------------------ Token Navigation Helpers ------------------

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        """Check if we have reached the end of the token stream."""
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        """Consume and return the current token."""
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _check(self, token_type: TokenType) -> bool:
        """Check if the current token matches token_type without consuming."""
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _match(self, *token_types: TokenType) -> bool:
        """Consume current token if it matches any of token_types."""
        for t in token_types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, error_message: str) -> Token:
        """Consume expected token or raise a ParserError."""
        if self._check(token_type):
            return self._advance()
        current = self._peek()
        raise ParserError(
            error_message,
            line=current.line,
            column=current.column,
            source_code=self.source_code,
        )

    def _skip_newlines(self) -> None:
        """Skip any consecutive newlines."""
        while self._match(TokenType.NEWLINE):
            pass

    # ------------------ Public Parse Entry Point ------------------

    def parse(self) -> Program:
        """Parse the complete token stream into a Program node."""
        statements: list[Statement] = []
        self._skip_newlines()

        while not self._is_at_end():
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()

        first_tok = self.tokens[0] if self.tokens else Token(TokenType.EOF, None, 1, 1)
        return Program(
            line=first_tok.line,
            column=first_tok.column,
            statements=statements,
        )

    # ------------------ Statement Parsing ------------------

    def _statement(self) -> Statement:
        """statement -> var_declaration | if_statement | while_statement | block | expr_statement"""
        self._skip_newlines()

        if self._match(TokenType.LET):
            return self._var_declaration()

        if self._match(TokenType.IF):
            return self._if_statement()

        if self._match(TokenType.WHILE):
            return self._while_statement()

        if self._check(TokenType.LBRACE):
            return self._block()

        return self._expression_statement()

    def _var_declaration(self) -> VariableDeclaration:
        """var_declaration -> 'let' IDENTIFIER '=' expression"""
        let_token = self._previous()
        name_token = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self._consume(TokenType.ASSIGN, f"Expected '=' after variable name '{name_token.value}'")
        initializer = self._expression()

        # Optional semicolon or newline statement terminator
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)

        return VariableDeclaration(
            line=let_token.line,
            column=let_token.column,
            name=name_token.value,
            initializer=initializer,
        )

    def _if_statement(self) -> IfStatement:
        """if_statement -> 'if' expression block ( 'else' ( block | if_statement ) )?"""
        if_token = self._previous()
        condition = self._expression()

        self._skip_newlines()
        then_branch = self._block()

        else_branch: Optional[Statement] = None
        self._skip_newlines()
        if self._match(TokenType.ELSE):
            self._skip_newlines()
            if self._match(TokenType.IF):
                else_branch = self._if_statement()
            else:
                else_branch = self._block()

        return IfStatement(
            line=if_token.line,
            column=if_token.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _while_statement(self) -> WhileStatement:
        """while_statement -> 'while' expression block"""
        while_token = self._previous()
        condition = self._expression()
        self._skip_newlines()
        body = self._block()

        return WhileStatement(
            line=while_token.line,
            column=while_token.column,
            condition=condition,
            body=body,
        )

    def _block(self) -> Block:
        """block -> '{' statement* '}'"""
        brace_token = self._consume(TokenType.LBRACE, "Expected '{' to begin block")
        statements: list[Statement] = []

        self._skip_newlines()
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()

        self._consume(TokenType.RBRACE, "Expected '}' after block")
        return Block(
            line=brace_token.line,
            column=brace_token.column,
            statements=statements,
        )

    def _expression_statement(self) -> ExpressionStatement:
        """expr_statement -> expression ( ';' | '\\n' )?"""
        expr = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return ExpressionStatement(
            line=expr.line,
            column=expr.column,
            expression=expr,
        )

    # ------------------ Expression Parsing ------------------

    def _expression(self) -> Expression:
        """expression -> assignment"""
        return self._assignment()

    def _assignment(self) -> Expression:
        """assignment -> IDENTIFIER '=' assignment | equality"""
        expr = self._equality()

        if self._match(TokenType.ASSIGN):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expr, Identifier):
                return Assignment(
                    line=equals.line,
                    column=equals.column,
                    name=expr.name,
                    value=value,
                )

            raise ParserError(
                f"Invalid assignment target at line {equals.line}",
                line=equals.line,
                column=equals.column,
                source_code=self.source_code,
            )

        return expr

    def _equality(self) -> Expression:
        """equality -> comparison ( ( '==' | '!=' ) comparison )*"""
        expr = self._comparison()

        while self._match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self._previous().value
            right = self._comparison()
            expr = BinaryOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr

    def _comparison(self) -> Expression:
        """comparison -> term ( ( '>' | '>=' | '<' | '<=' ) term )*"""
        expr = self._term()

        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous().value
            right = self._term()
            expr = BinaryOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr

    def _term(self) -> Expression:
        """term -> factor ( ( '+' | '-' ) factor )*"""
        expr = self._factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().value
            right = self._factor()
            expr = BinaryOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr

    def _factor(self) -> Expression:
        """factor -> unary ( ( '*' | '/' | '%' ) unary )*"""
        expr = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.MODULO):
            operator = self._previous().value
            right = self._unary()
            expr = BinaryOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr

    def _unary(self) -> Expression:
        """unary -> ( '!' | '-' ) unary | call"""
        if self._match(TokenType.BANG, TokenType.MINUS):
            op_tok = self._previous()
            operand = self._unary()
            return UnaryOp(
                line=op_tok.line,
                column=op_tok.column,
                operator=op_tok.value,
                operand=operand,
            )

        return self._call()

    def _call(self) -> Expression:
        """call -> primary ( '(' arguments? ')' )*"""
        expr = self._primary()

        while True:
            if self._match(TokenType.LPAREN):
                expr = self._finish_call(expr)
            else:
                break

        return expr

    def _finish_call(self, callee: Expression) -> CallExpression:
        """Parse argument list for function call: ( arg1, arg2, ... )"""
        args: list[Expression] = []

        self._skip_newlines()
        if not self._check(TokenType.RPAREN):
            while True:
                self._skip_newlines()
                args.append(self._expression())
                self._skip_newlines()
                if not self._match(TokenType.COMMA):
                    break

        paren = self._consume(TokenType.RPAREN, "Expected ')' after arguments")
        return CallExpression(
            line=callee.line,
            column=callee.column,
            callee=callee,
            arguments=args,
        )

    def _primary(self) -> Expression:
        """primary -> NUMBER | STRING | TRUE | FALSE | IDENTIFIER | '(' expression ')'"""
        if self._match(TokenType.NUMBER):
            tok = self._previous()
            return NumberLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.STRING):
            tok = self._previous()
            return StringLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.TRUE, TokenType.FALSE):
            tok = self._previous()
            return BooleanLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.IDENTIFIER):
            tok = self._previous()
            return Identifier(line=tok.line, column=tok.column, name=tok.value)

        if self._match(TokenType.LPAREN):
            lparen = self._previous()
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return Grouping(line=lparen.line, column=lparen.column, expression=expr)

        current = self._peek()
        raise ParserError(
            f"Expected expression, found '{current.value or current.type.name}'",
            line=current.line,
            column=current.column,
            source_code=self.source_code,
        )

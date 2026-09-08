"""FlowLang Recursive-Descent Parser for Python-style Syntax.

Parses indentation suites (: + INDENT ... DEDENT), if/elif/else, while, for,
direct assignments, augmented assignments (+=, -=, *=, /=), and logical expressions.
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
    ForStatement,
    Assignment,
    AugmentedAssignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NoneLiteral,
    Identifier,
)


class Parser:
    """Recursive-descent parser for Python-like FlowLang."""

    def __init__(self, tokens: list[Token], source_code: Optional[str] = None):
        self.tokens = tokens
        self.source_code = source_code
        self.pos = 0

    # ------------------ Token Navigation Helpers ------------------

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _match(self, *token_types: TokenType) -> bool:
        for t in token_types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, error_message: str) -> Token:
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
        while self._match(TokenType.NEWLINE):
            pass

    # ------------------ Public Parse Entry Point ------------------

    def parse(self) -> Program:
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
        """statement -> if_statement | while_statement | for_statement | let_statement | expr_statement"""
        self._skip_newlines()

        if self._match(TokenType.IF):
            return self._if_statement()

        if self._match(TokenType.WHILE):
            return self._while_statement()

        if self._match(TokenType.FOR):
            return self._for_statement()

        if self._match(TokenType.LET):
            return self._let_statement()

        return self._expression_statement()

    def _suite(self) -> Statement:
        """suite -> ':' ( NEWLINE INDENT statement+ DEDENT | statement )"""
        self._consume(TokenType.COLON, "Expected ':' after condition")

        if self._match(TokenType.NEWLINE):
            indent_tok = self._consume(TokenType.INDENT, "Expected indented block")
            statements: list[Statement] = []

            self._skip_newlines()
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                stmt = self._statement()
                if stmt is not None:
                    statements.append(stmt)
                self._skip_newlines()

            self._consume(TokenType.DEDENT, "Expected dedent at end of block")
            return Block(
                line=indent_tok.line,
                column=indent_tok.column,
                statements=statements,
            )

        stmt = self._statement()
        return Block(
            line=stmt.line,
            column=stmt.column,
            statements=[stmt],
        )

    def _if_statement(self) -> IfStatement:
        """if_statement -> 'if' expression suite ('elif' expression suite)* ('else' suite)?"""
        if_tok = self._previous()
        condition = self._expression()
        then_branch = self._suite()

        else_branch: Optional[Statement] = None
        self._skip_newlines()

        if self._match(TokenType.ELIF):
            else_branch = self._if_statement()
        elif self._match(TokenType.ELSE):
            else_branch = self._suite()

        return IfStatement(
            line=if_tok.line,
            column=if_tok.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _while_statement(self) -> WhileStatement:
        """while_statement -> 'while' expression suite"""
        while_tok = self._previous()
        condition = self._expression()
        body = self._suite()

        return WhileStatement(
            line=while_tok.line,
            column=while_tok.column,
            condition=condition,
            body=body,
        )

    def _for_statement(self) -> ForStatement:
        """for_statement -> 'for' IDENTIFIER 'in' expression suite"""
        for_tok = self._previous()
        target_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'for'")
        self._consume(TokenType.IN, "Expected 'in' after for loop variable")
        iterable = self._expression()
        body = self._suite()

        return ForStatement(
            line=for_tok.line,
            column=for_tok.column,
            target=target_tok.value,
            iterable=iterable,
            body=body,
        )

    def _let_statement(self) -> VariableDeclaration:
        """let_statement -> 'let' IDENTIFIER '=' expression (optional)"""
        let_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self._consume(TokenType.ASSIGN, f"Expected '=' after variable name '{name_tok.value}'")
        initializer = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)

        return VariableDeclaration(
            line=let_tok.line,
            column=let_tok.column,
            name=name_tok.value,
            initializer=initializer,
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
        return self._assignment()

    def _assignment(self) -> Expression:
        """assignment -> IDENTIFIER ('=' | '+=' | '-=' | '*=' | '/=') assignment | logical_or"""
        expr = self._logical_or()

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

        if self._match(TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN):
            op_tok = self._previous()
            value = self._assignment()

            if isinstance(expr, Identifier):
                return AugmentedAssignment(
                    line=op_tok.line,
                    column=op_tok.column,
                    name=expr.name,
                    operator=op_tok.value,
                    value=value,
                )

            raise ParserError(
                f"Invalid assignment target at line {op_tok.line}",
                line=op_tok.line,
                column=op_tok.column,
                source_code=self.source_code,
            )

        return expr

    def _logical_or(self) -> Expression:
        """logical_or -> logical_and ( 'or' logical_and )*"""
        expr = self._logical_and()

        while self._match(TokenType.OR):
            op = self._previous().value
            right = self._logical_and()
            expr = LogicalOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=op,
                right=right,
            )

        return expr

    def _logical_and(self) -> Expression:
        """logical_and -> logical_not ( 'and' logical_not )*"""
        expr = self._logical_not()

        while self._match(TokenType.AND):
            op = self._previous().value
            right = self._logical_not()
            expr = LogicalOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=op,
                right=right,
            )

        return expr

    def _logical_not(self) -> Expression:
        """logical_not -> 'not' logical_not | equality"""
        if self._match(TokenType.NOT):
            op_tok = self._previous()
            operand = self._logical_not()
            return UnaryOp(
                line=op_tok.line,
                column=op_tok.column,
                operator="not",
                operand=operand,
            )

        return self._equality()

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
        """primary -> NUMBER | STRING | TRUE | FALSE | NONE | IDENTIFIER | '(' expression ')'"""
        if self._match(TokenType.NUMBER):
            tok = self._previous()
            return NumberLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.STRING):
            tok = self._previous()
            return StringLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.TRUE, TokenType.FALSE):
            tok = self._previous()
            return BooleanLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.NONE):
            tok = self._previous()
            return NoneLiteral(line=tok.line, column=tok.column)

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

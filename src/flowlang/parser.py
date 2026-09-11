"""FlowLang Recursive-Descent Parser for FlowLang V1.

Parses brace-delimited blocks ({ ... }), typed and dynamic variable declarations,
if/elif/else, while, do-while, for loops with C-style headers, functions (dfn),
return statements, and C-style operator precedence with left-to-right associativity.
"""

from typing import Optional
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
    DoWhileStatement,
    ForStatement,
    ForInStatement,
    FunctionDeclaration,
    ReturnStatement,
    Assignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    ListLiteral,
    BrackLiteral,
    DictLiteral,
    IndexAccess,
    IndexAssignment,
    MemberAccess,
    NumberLiteral,
    StringLiteral,
    CharLiteral,
    BooleanLiteral,
    Identifier,
)


class Parser:
    """Recursive-descent parser for FlowLang V1."""

    def __init__(self, tokens: list[Token], source_code: Optional[str] = None):
        self.tokens = tokens
        self.source_code = source_code
        self.pos = 0

    # ------------------ Token Navigation Helpers ------------------

    def _peek(self, offset: int = 0) -> Token:
        target = self.pos + offset
        if target < len(self.tokens):
            return self.tokens[target]
        return self.tokens[-1]

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
        """Parse a statement."""
        self._skip_newlines()

        if self._check(TokenType.IF):
            self._advance()
            return self._if_statement()

        if self._check(TokenType.WHILE):
            self._advance()
            return self._while_statement()

        if self._check(TokenType.DO):
            self._advance()
            return self._do_while_statement()

        if self._check(TokenType.FOR):
            self._advance()
            return self._for_statement()

        if self._check(TokenType.DFN):
            self._advance()
            return self._dfn_statement()

        if self._check(TokenType.RETURN):
            self._advance()
            return self._return_statement()

        # Variable declarations: lit / int / flt / str / char / bool / list / brack / dict <id> = <expr>
        type_tokens = (
            TokenType.LIT,
            TokenType.INT,
            TokenType.FLT,
            TokenType.STR,
            TokenType.CHAR_TYPE,
            TokenType.BOOL_TYPE,
            TokenType.LIST,
            TokenType.BRACK,
            TokenType.DICT,
        )
        if self._check_any(*type_tokens) and self._peek(1).type == TokenType.IDENTIFIER:
            return self._var_declaration()

        return self._expression_statement()

    def _check_any(self, *types: TokenType) -> bool:
        return any(self._check(t) for t in types)

    def _block(self) -> Block:
        """block -> '{' statement* '}'"""
        lbrace = self._consume(TokenType.LBRACE, "Expected '{' to start block")
        statements: list[Statement] = []

        self._skip_newlines()
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()

        self._consume(TokenType.RBRACE, "Expected '}' at end of block")
        return Block(
            line=lbrace.line,
            column=lbrace.column,
            statements=statements,
        )

    def _var_declaration(self) -> VariableDeclaration:
        """var_decl -> (lit | int | flt | str | char | bool) IDENTIFIER '=' expression"""
        type_tok = self._advance()
        name_tok = self._consume(TokenType.IDENTIFIER, f"Expected variable name after '{type_tok.value}'")
        self._consume(TokenType.ASSIGN, f"Expected '=' after variable name '{name_tok.value}'")
        initializer = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)

        return VariableDeclaration(
            line=type_tok.line,
            column=type_tok.column,
            type_name=type_tok.value,
            name=name_tok.value,
            initializer=initializer,
        )

    def _if_statement(self) -> IfStatement:
        """if_statement -> 'if' expression block ('elif' expression block)* ('else' block)?"""
        if_tok = self._previous()
        condition = self._expression()
        self._skip_newlines()
        then_branch = self._block()

        else_branch: Optional[Statement] = None
        self._skip_newlines()

        if self._match(TokenType.ELIF):
            else_branch = self._if_statement()
        elif self._match(TokenType.ELSE):
            self._skip_newlines()
            else_branch = self._block()

        return IfStatement(
            line=if_tok.line,
            column=if_tok.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _while_statement(self) -> WhileStatement:
        """while_statement -> 'while' expression block"""
        while_tok = self._previous()
        condition = self._expression()
        self._skip_newlines()
        body = self._block()

        return WhileStatement(
            line=while_tok.line,
            column=while_tok.column,
            condition=condition,
            body=body,
        )

    def _do_while_statement(self) -> DoWhileStatement:
        """do_while_statement -> 'do' block 'while' expression"""
        do_tok = self._previous()
        self._skip_newlines()
        body = self._block()
        self._skip_newlines()
        self._consume(TokenType.WHILE, "Expected 'while' after 'do' block")
        condition = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)

        return DoWhileStatement(
            line=do_tok.line,
            column=do_tok.column,
            body=body,
            condition=condition,
        )

    def _has_semicolon_in_parens(self) -> bool:
        """Check if upcoming parenthesized clause contains semicolons (for header or range)."""
        if not self._check(TokenType.LPAREN):
            return False
        depth = 0
        i = 0
        while True:
            tok = self._peek(i)
            if tok.type == TokenType.EOF:
                break
            if tok.type == TokenType.LPAREN:
                depth += 1
            elif tok.type == TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    break
            elif tok.type == TokenType.SEMICOLON and depth == 1:
                return True
            i += 1
        return False

    def _for_statement(self) -> Statement:
        """for_statement -> V1 C-style loop or V2 collection/ranged loop"""
        for_tok = self._previous()
        target_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'for'")
        self._consume(TokenType.IN, "Expected 'in' after for loop variable")

        if self._has_semicolon_in_parens():
            self._consume(TokenType.LPAREN, "Expected '(' after 'in'")
            self._skip_newlines()

            init_expr = self._expression()
            self._consume(TokenType.SEMICOLON, "Expected ';' after for loop initialization")
            self._skip_newlines()

            cond_expr = self._expression()
            self._consume(TokenType.SEMICOLON, "Expected ';' after for loop condition")
            self._skip_newlines()

            update_expr = self._expression()
            self._skip_newlines()
            self._consume(TokenType.RPAREN, "Expected ')' after for loop header")
            self._skip_newlines()

            body = self._block()

            return ForStatement(
                line=for_tok.line,
                column=for_tok.column,
                target=target_tok.value,
                init_expr=init_expr,
                condition=cond_expr,
                update=update_expr,
                body=body,
            )

        # V2 Collection iteration: for i in iterable or for i in iterable(start; end; step)
        self._skip_newlines()
        iterable = self._expression()
        self._skip_newlines()

        range_args: Optional[list[Expression]] = None
        if self._match(TokenType.LPAREN):
            self._skip_newlines()
            start_expr = self._expression()
            self._consume(TokenType.SEMICOLON, "Expected ';' after range start")
            self._skip_newlines()
            end_expr = self._expression()
            self._skip_newlines()
            step_expr: Optional[Expression] = None
            if self._match(TokenType.SEMICOLON):
                self._skip_newlines()
                step_expr = self._expression()
                self._skip_newlines()
            self._consume(TokenType.RPAREN, "Expected ')' after range arguments")
            range_args = [start_expr, end_expr]
            if step_expr is not None:
                range_args.append(step_expr)

        self._skip_newlines()
        body = self._block()

        return ForInStatement(
            line=for_tok.line,
            column=for_tok.column,
            target=target_tok.value,
            iterable=iterable,
            range_args=range_args,
            body=body,
        )

    def _dfn_statement(self) -> FunctionDeclaration:
        """dfn_statement -> 'dfn' IDENTIFIER '(' params? ')' block"""
        dfn_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name after 'dfn'")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters: list[str] = []

        self._skip_newlines()
        if not self._check(TokenType.RPAREN):
            while True:
                self._skip_newlines()
                param_tok = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                parameters.append(param_tok.value)
                self._skip_newlines()
                if not self._match(TokenType.COMMA):
                    break

        self._consume(TokenType.RPAREN, "Expected ')' after parameter list")
        self._skip_newlines()
        body = self._block()

        return FunctionDeclaration(
            line=dfn_tok.line,
            column=dfn_tok.column,
            name=name_tok.value,
            parameters=parameters,
            body=body,
        )

    def _return_statement(self) -> ReturnStatement:
        """return_statement -> 'return' expression?"""
        ret_tok = self._previous()
        value: Optional[Expression] = None

        if not self._check_any(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            value = self._expression()

        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return ReturnStatement(
            line=ret_tok.line,
            column=ret_tok.column,
            expression=value,
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

    # ------------------ Expression Parsing (C Precedence) ------------------

    def _expression(self) -> Expression:
        return self._assignment()

    def _assignment(self) -> Expression:
        """assignment -> IDENTIFIER '=' assignment | logical_or"""
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

            if isinstance(expr, IndexAccess):
                return IndexAssignment(
                    line=equals.line,
                    column=equals.column,
                    target=expr.target,
                    index=expr.index,
                    value=value,
                )

            raise ParserError(
                f"Invalid assignment target at line {equals.line}",
                line=equals.line,
                column=equals.column,
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
        """logical_and -> equality ( 'and' equality )*"""
        expr = self._equality()

        while self._match(TokenType.AND):
            op = self._previous().value
            right = self._equality()
            expr = LogicalOp(
                line=expr.line,
                column=expr.column,
                left=expr,
                operator=op,
                right=right,
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
        """comparison -> term ( ( '<' | '<=' | '>' | '>=' ) term )*"""
        expr = self._term()

        while self._match(TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
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
        """unary -> ( '-' | 'not' ) unary | call"""
        if self._match(TokenType.MINUS):
            op_tok = self._previous()
            operand = self._unary()
            return UnaryOp(
                line=op_tok.line,
                column=op_tok.column,
                operator="-",
                operand=operand,
            )

        if self._match(TokenType.NOT):
            op_tok = self._previous()
            operand = self._unary()
            return UnaryOp(
                line=op_tok.line,
                column=op_tok.column,
                operator="not",
                operand=operand,
            )

        return self._call()

    def _call(self) -> Expression:
        """call -> primary ( '(' arguments? ')' | '[' index ']' | '.' IDENTIFIER )*"""
        expr = self._primary()

        while True:
            if self._check(TokenType.LPAREN):
                if self._has_semicolon_in_parens():
                    break
                self._advance()
                expr = self._finish_call(expr)
            elif self._match(TokenType.LBRACKET):
                bracket = self._previous()
                self._skip_newlines()
                index_expr = self._expression()
                self._skip_newlines()
                self._consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexAccess(
                    line=bracket.line,
                    column=bracket.column,
                    target=expr,
                    index=index_expr,
                )
            elif self._match(TokenType.DOT):
                dot = self._previous()
                member_tok = self._consume(TokenType.IDENTIFIER, "Expected member name after '.'")
                expr = MemberAccess(
                    line=dot.line,
                    column=dot.column,
                    target=expr,
                    member=member_tok.value,
                )
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
        """primary -> NUMBER | STRING | CHAR | TRUE | FALSE | IDENTIFIER | type/say identifier | list/dict/brack | '(' expression ')'"""
        if self._match(TokenType.NUMBER):
            tok = self._previous()
            return NumberLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.STRING):
            tok = self._previous()
            return StringLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.CHAR):
            tok = self._previous()
            return CharLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.TRUE, TokenType.FALSE):
            tok = self._previous()
            return BooleanLiteral(line=tok.line, column=tok.column, value=tok.value)

        if self._match(TokenType.IDENTIFIER):
            tok = self._previous()
            return Identifier(line=tok.line, column=tok.column, name=tok.value)

        # Allow 'say' as callee identifier
        if self._match(TokenType.SAY):
            tok = self._previous()
            return Identifier(line=tok.line, column=tok.column, name="say")

        # Allow type names as conversion function callee identifiers e.g. int(input()), flt(input()), bk(input())
        if self._match(TokenType.INT, TokenType.FLT, TokenType.STR, TokenType.CHAR_TYPE, TokenType.BOOL_TYPE, TokenType.LIST, TokenType.BRACK, TokenType.DICT):
            tok = self._previous()
            name = "char" if tok.type == TokenType.CHAR_TYPE else ("bool" if tok.type == TokenType.BOOL_TYPE else tok.value)
            return Identifier(line=tok.line, column=tok.column, name=name)

        # List literal: [ e1, e2, ... ]
        if self._match(TokenType.LBRACKET):
            lbracket = self._previous()
            elements: list[Expression] = []
            self._skip_newlines()
            if not self._check(TokenType.RBRACKET):
                while True:
                    self._skip_newlines()
                    elements.append(self._expression())
                    self._skip_newlines()
                    if not self._match(TokenType.COMMA):
                        break
                    self._skip_newlines()
            self._consume(TokenType.RBRACKET, "Expected ']' after list elements")
            return ListLiteral(line=lbracket.line, column=lbracket.column, elements=elements)

        # Dict literal: << k1: v1, k2: v2, ... >>
        if self._match(TokenType.LDICT):
            ldict = self._previous()
            entries: list[tuple[Expression, Expression]] = []
            self._skip_newlines()
            if not self._check(TokenType.RDICT):
                while True:
                    self._skip_newlines()
                    key_expr = self._expression()
                    self._skip_newlines()
                    self._consume(TokenType.COLON, "Expected ':' after dictionary key")
                    self._skip_newlines()
                    val_expr = self._expression()
                    entries.append((key_expr, val_expr))
                    self._skip_newlines()
                    if not self._match(TokenType.COMMA):
                        break
                    self._skip_newlines()
            self._consume(TokenType.RDICT, "Expected '>>' after dictionary entries")
            return DictLiteral(line=ldict.line, column=ldict.column, entries=entries)

        # Parenthesized: empty brack (), brack literal (1, 2, ...), or grouping (expr)
        if self._match(TokenType.LPAREN):
            lparen = self._previous()
            self._skip_newlines()
            # Empty brack: ()
            if self._match(TokenType.RPAREN):
                return BrackLiteral(line=lparen.line, column=lparen.column, elements=[])

            first = self._expression()
            self._skip_newlines()
            if self._match(TokenType.COMMA):
                elements = [first]
                self._skip_newlines()
                if not self._check(TokenType.RPAREN):
                    while True:
                        self._skip_newlines()
                        elements.append(self._expression())
                        self._skip_newlines()
                        if not self._match(TokenType.COMMA):
                            break
                        self._skip_newlines()
                self._consume(TokenType.RPAREN, "Expected ')' after brack elements")
                return BrackLiteral(line=lparen.line, column=lparen.column, elements=elements)

            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return Grouping(line=lparen.line, column=lparen.column, expression=first)

        current = self._peek()
        raise ParserError(
            f"Expected expression, found '{current.value or current.type.name}'",
            line=current.line,
            column=current.column,
            source_code=self.source_code,
        )

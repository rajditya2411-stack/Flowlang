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
    ImportStatement,
    Assignment,
    CompoundAssignment,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    CallExpression,
    ListLiteral,
    BrackLiteral,
    DictLiteral,
    StructLiteral,
    IndexAccess,
    IndexAssignment,
    MemberAccess,
    NumberLiteral,
    StringLiteral,
    CharLiteral,
    BooleanLiteral,
    Identifier,
    BreakStatement,
    ContinueStatement,
    StructDeclaration,
    EnumDeclaration,
    TryCatchStatement,
    RaiseStatement,
    GlobalStatement,
)


class Parser:
    """Recursive-descent parser for FlowLang V1."""

    def __init__(self, tokens: list[Token], source_code: Optional[str] = None):
        self.tokens = tokens
        self.source_code = source_code
        self.pos = 0
        self._in_for_in_iterable = False

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

        if self._check(TokenType.IMPORT):
            self._advance()
            return self._import_statement()

        if self._check(TokenType.BREAK):
            tok = self._advance()
            self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
            return BreakStatement(line=tok.line, column=tok.column)

        if self._check(TokenType.CONTINUE):
            tok = self._advance()
            self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
            return ContinueStatement(line=tok.line, column=tok.column)

        if self._check(TokenType.STRUCT):
            self._advance()
            return self._struct_declaration()

        if self._check(TokenType.ENUM):
            self._advance()
            return self._enum_declaration()

        if self._check(TokenType.TRY):
            self._advance()
            return self._try_catch_statement()

        if self._check(TokenType.RAISE):
            self._advance()
            return self._raise_statement()

        if self._check(TokenType.GLOBAL):
            self._advance()
            return self._global_statement()

        if self._check(TokenType.LBRACE):
            return self._block()

        # Variable declarations: (mut)? (lit | int | flt | str | char | bool | list | brack | func | StructName | EnumName) <id> = <expr>
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
            TokenType.FUNCTION_TYPE,
        )
        if self._check(TokenType.IDENTIFIER) and self._peek(0).value == "none" and self._peek(1).type == TokenType.IDENTIFIER:
            none_tok = self._peek(0)
            raise ParserError(
                "'none' is a runtime value, not a type; cannot declare a variable of type 'none'",
                line=none_tok.line,
                column=none_tok.column,
                source_code=self.source_code,
            )

        if self._check(TokenType.MUT):
            self._advance()
            return self._var_declaration(is_mutable=True)

        if self._check_any(*type_tokens) and self._peek(1).type == TokenType.IDENTIFIER:
            return self._var_declaration(is_mutable=False)

        # Custom struct type: Name var = ...
        if (
            self._check(TokenType.IDENTIFIER)
            and self._peek(1).type == TokenType.IDENTIFIER
            and self._peek(0).value != "none"
            and self._peek(2).type == TokenType.ASSIGN
        ):
            return self._var_declaration(is_mutable=False)

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

    def _struct_declaration(self) -> StructDeclaration:
        """struct_decl -> 'struct' IDENTIFIER '=' '<<' (type IDENTIFIER (',' type IDENTIFIER)*)? '>>'"""
        struct_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected struct name after 'struct'")
        self._consume(TokenType.ASSIGN, "Expected '=' after struct name")
        self._consume(TokenType.LDICT, "Expected '<<' to start struct definition")
        fields: list[tuple[str, str]] = []
        self._skip_newlines()
        if not self._check(TokenType.RDICT):
            while True:
                self._skip_newlines()
                type_tokens = (
                    TokenType.LIT,
                    TokenType.INT,
                    TokenType.FLT,
                    TokenType.STR,
                    TokenType.CHAR_TYPE,
                    TokenType.BOOL_TYPE,
                    TokenType.LIST,
                    TokenType.BRACK,
                    TokenType.FUNCTION_TYPE,
                    TokenType.IDENTIFIER,
                )
                if self._check_any(*type_tokens):
                    t_tok = self._advance()
                    t_name = "char" if t_tok.type == TokenType.CHAR_TYPE else ("bool" if t_tok.type == TokenType.BOOL_TYPE else ("func" if t_tok.type == TokenType.FUNCTION_TYPE else t_tok.value))
                    f_name_tok = self._consume(TokenType.IDENTIFIER, f"Expected field name after type '{t_name}' in struct '{name_tok.value}'")
                    fields.append((f_name_tok.value, t_name))
                else:
                    cur = self._peek()
                    raise ParserError(
                        f"Expected field type in struct definition, got '{cur.value or cur.type.name}'",
                        line=cur.line,
                        column=cur.column,
                        source_code=self.source_code,
                    )
                self._skip_newlines()
                if not (self._match(TokenType.COMMA) or self._match(TokenType.SEMICOLON)):
                    break
                self._skip_newlines()
        self._consume(TokenType.RDICT, "Expected '>>' at end of struct definition")
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return StructDeclaration(
            line=struct_tok.line,
            column=struct_tok.column,
            name=name_tok.value,
            fields=fields,
        )

    def _var_declaration(self, is_mutable: bool = False) -> VariableDeclaration:
        """var_decl -> ('mut')? (type | IDENTIFIER) IDENTIFIER '=' expression"""
        type_tok = self._advance()
        type_name = "char" if type_tok.type == TokenType.CHAR_TYPE else ("bool" if type_tok.type == TokenType.BOOL_TYPE else ("func" if type_tok.type == TokenType.FUNCTION_TYPE else type_tok.value))
        name_tok = self._consume(TokenType.IDENTIFIER, f"Expected variable name after '{type_name}'")
        if name_tok.value == "none":
            raise ParserError(
                "Cannot use reserved identifier 'none' as a variable name",
                line=name_tok.line,
                column=name_tok.column,
                source_code=self.source_code,
            )
        self._consume(TokenType.ASSIGN, f"Expected '=' after variable name '{name_tok.value}'")
        initializer = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)

        return VariableDeclaration(
            line=type_tok.line,
            column=type_tok.column,
            type_name=type_name,
            name=name_tok.value,
            initializer=initializer,
            is_mutable=is_mutable,
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
        self._in_for_in_iterable = True
        try:
            iterable = self._expression()
        finally:
            self._in_for_in_iterable = False
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
        """dfn_statement -> 'dfn' IDENTIFIER '(' params? ')' '->' return_type block"""
        dfn_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name after 'dfn'")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters: list[tuple[str, str]] = []

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
            TokenType.FUNCTION_TYPE,
        )

        self._skip_newlines()
        if not self._check(TokenType.RPAREN):
            while True:
                self._skip_newlines()
                type_tok = None
                if (self._check_any(*type_tokens) or (self._check(TokenType.IDENTIFIER) and self._peek(1).type == TokenType.IDENTIFIER)):
                    type_tok = self._advance()
                param_tok = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                if type_tok is None:
                    param_type = "lit"
                elif type_tok.type == TokenType.CHAR_TYPE:
                    param_type = "char"
                elif type_tok.type == TokenType.BOOL_TYPE:
                    param_type = "bool"
                elif type_tok.type == TokenType.FUNCTION_TYPE:
                    param_type = "func"
                else:
                    param_type = type_tok.value
                parameters.append((param_tok.value, param_type))
                self._skip_newlines()
                if not self._match(TokenType.COMMA):
                    break

        self._consume(TokenType.RPAREN, "Expected ')' after parameter list")
        self._skip_newlines()

        # Section 32: Return type declarations are REQUIRED
        self._consume(TokenType.ARROW, "Expected '->' return type declaration (return types are required in V2, e.g. '-> int' or '-> lit')")
        self._skip_newlines()

        if self._check(TokenType.IDENTIFIER) and self._peek().value == "none":
            cur = self._peek()
            raise ParserError(
                "The 'none' type is not a valid user-facing return type in FlowLang V2 (use '-> lit' for functions returning no value)",
                line=cur.line,
                column=cur.column,
                source_code=self.source_code,
            )

        if not (self._check_any(*type_tokens) or self._check(TokenType.IDENTIFIER)):
            cur = self._peek()
            raise ParserError(
                f"Expected valid return type after '->', got '{cur.value or cur.type.name}'",
                line=cur.line,
                column=cur.column,
                source_code=self.source_code,
            )

        return_type_tok = self._advance()
        if return_type_tok.type == TokenType.CHAR_TYPE:
            return_type = "char"
        elif return_type_tok.type == TokenType.BOOL_TYPE:
            return_type = "bool"
        elif return_type_tok.type == TokenType.FUNCTION_TYPE:
            return_type = "func"
        else:
            return_type = return_type_tok.value

        self._skip_newlines()
        body = self._block()

        return FunctionDeclaration(
            line=dfn_tok.line,
            column=dfn_tok.column,
            name=name_tok.value,
            parameters=parameters,
            return_type=return_type,
            body=body,
        )

    def _enum_declaration(self) -> EnumDeclaration:
        """enum_decl -> 'enum' IDENTIFIER '=' '<<' (IDENTIFIER (',' IDENTIFIER)*)? '>>'"""
        enum_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected enum name after 'enum'")
        self._consume(TokenType.ASSIGN, "Expected '=' after enum name")
        self._consume(TokenType.LDICT, "Expected '<<' to start enum definition")
        members: list[str] = []
        seen_members: set[str] = set()
        self._skip_newlines()
        if not self._check(TokenType.RDICT):
            while True:
                self._skip_newlines()
                m_tok = self._consume(TokenType.IDENTIFIER, f"Expected enum member name in enum '{name_tok.value}'")
                if m_tok.value in seen_members:
                    raise ParserError(
                        f"Duplicate member '{m_tok.value}' in enum '{name_tok.value}'",
                        line=m_tok.line,
                        column=m_tok.column,
                        source_code=self.source_code,
                    )
                seen_members.add(m_tok.value)
                members.append(m_tok.value)
                self._skip_newlines()
                if not (self._match(TokenType.COMMA) or self._match(TokenType.SEMICOLON)):
                    break
                self._skip_newlines()
        self._consume(TokenType.RDICT, "Expected '>>' at end of enum definition")
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return EnumDeclaration(
            line=enum_tok.line,
            column=enum_tok.column,
            name=name_tok.value,
            members=members,
        )

    def _try_catch_statement(self) -> TryCatchStatement:
        """try_catch -> 'try' block 'catch' '(' 'str' IDENTIFIER ')' block"""
        try_tok = self._previous()
        self._skip_newlines()
        try_block = self._block()
        self._skip_newlines()
        self._consume(TokenType.CATCH, "Expected 'catch' after try block")
        self._consume(TokenType.LPAREN, "Expected '(' after 'catch'")
        self._skip_newlines()
        err_type_tok = self._consume(TokenType.STR, "Expected 'str' error type in catch clause")
        err_name_tok = self._consume(TokenType.IDENTIFIER, "Expected error variable name after 'str'")
        self._consume(TokenType.RPAREN, "Expected ')' after catch parameter")
        self._skip_newlines()
        catch_block = self._block()
        return TryCatchStatement(
            line=try_tok.line,
            column=try_tok.column,
            try_block=try_block,
            error_type="str",
            error_name=err_name_tok.value,
            catch_block=catch_block,
        )

    def _raise_statement(self) -> RaiseStatement:
        """raise_statement -> 'raise' expression"""
        raise_tok = self._previous()
        expr = self._expression()
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return RaiseStatement(
            line=raise_tok.line,
            column=raise_tok.column,
            expression=expr,
        )

    def _global_statement(self) -> GlobalStatement:
        """global_statement -> 'global' IDENTIFIER"""
        global_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'global'")
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return GlobalStatement(
            line=global_tok.line,
            column=global_tok.column,
            name=name_tok.value,
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

    def _import_statement(self) -> ImportStatement:
        """import_statement -> 'import' IDENTIFIER ( ';' | '\\n' )?"""
        import_tok = self._previous()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected module name after 'import'")
        self._match(TokenType.SEMICOLON, TokenType.NEWLINE)
        return ImportStatement(
            line=import_tok.line,
            column=import_tok.column,
            module_name=name_tok.value,
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
        """assignment -> IDENTIFIER ('=' | '+=' | '-=' | '*=' | '//=' | '%=') assignment | logical_or"""
        expr = self._logical_or()

        compound_ops = {
            TokenType.PLUS_EQUAL: "+=",
            TokenType.MINUS_EQUAL: "-=",
            TokenType.STAR_EQUAL: "*=",
            TokenType.SLASH_SLASH_EQUAL: "//=",
            TokenType.MODULO_EQUAL: "%=",
        }
        for tok_type, op_str in compound_ops.items():
            if self._match(tok_type):
                op_tok = self._previous()
                value = self._assignment()
                if isinstance(expr, (Identifier, IndexAccess)):
                    return CompoundAssignment(
                        line=op_tok.line,
                        column=op_tok.column,
                        target=expr,
                        operator=op_str,
                        value=value,
                    )
                raise ParserError(
                    f"Invalid compound assignment target at line {op_tok.line}",
                    line=op_tok.line,
                    column=op_tok.column,
                    source_code=self.source_code,
                )

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
            op_tok = self._previous()
            if isinstance(expr, BinaryOp) and expr.operator in ("<", "<=", ">", ">=", "==", "!="):
                raise ParserError(
                    "Chained comparisons are not supported; use 'and' (e.g., 'a == b and b == c')",
                    line=op_tok.line,
                    column=op_tok.column,
                    source_code=self.source_code,
                )
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
            op_tok = self._previous()
            if isinstance(expr, BinaryOp) and expr.operator in ("<", "<=", ">", ">=", "==", "!="):
                raise ParserError(
                    "Chained comparisons are not supported; use 'and' (e.g., 'a < b and b < c')",
                    line=op_tok.line,
                    column=op_tok.column,
                    source_code=self.source_code,
                )
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
        """factor -> unary ( ( '*' | '/' | '//' | '%' ) unary )*"""
        expr = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.SLASH_SLASH, TokenType.MODULO):
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
        if self._match(TokenType.PLUS):
            op_tok = self._previous()
            raise ParserError(
                "Unary '+' is not supported; positive numbers are written without a sign",
                line=op_tok.line,
                column=op_tok.column,
                source_code=self.source_code,
            )

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
                if self._in_for_in_iterable and self._has_semicolon_in_parens():
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
        """Parse argument list for function call: ( arg1, arg2, ... ) or ( arg1; arg2; ... )"""
        args: list[Expression] = []

        self._skip_newlines()
        if not self._check(TokenType.RPAREN):
            while True:
                self._skip_newlines()
                args.append(self._expression())
                self._skip_newlines()
                if not (self._match(TokenType.COMMA) or self._match(TokenType.SEMICOLON)):
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

        # Dict or Struct literal: << k1: v1, ... >> or << v1, v2, ... >>
        if self._match(TokenType.LDICT):
            ldict = self._previous()
            self._skip_newlines()
            if self._check(TokenType.RDICT):
                self._advance()
                return DictLiteral(line=ldict.line, column=ldict.column, entries=[])

            first_expr = self._expression()
            self._skip_newlines()
            if self._match(TokenType.COLON):
                self._skip_newlines()
                val_expr = self._expression()
                entries: list[tuple[Expression, Expression]] = [(first_expr, val_expr)]
                self._skip_newlines()
                while self._match(TokenType.COMMA):
                    self._skip_newlines()
                    if self._check(TokenType.RDICT):
                        break
                    key_expr = self._expression()
                    self._skip_newlines()
                    self._consume(TokenType.COLON, "Expected ':' after dictionary key")
                    self._skip_newlines()
                    v_expr = self._expression()
                    entries.append((key_expr, v_expr))
                    self._skip_newlines()
                self._consume(TokenType.RDICT, "Expected '>>' after dictionary entries")
                return DictLiteral(line=ldict.line, column=ldict.column, entries=entries)
            else:
                values: list[Expression] = [first_expr]
                self._skip_newlines()
                while self._match(TokenType.COMMA):
                    self._skip_newlines()
                    if self._check(TokenType.RDICT):
                        break
                    values.append(self._expression())
                    self._skip_newlines()
                self._consume(TokenType.RDICT, "Expected '>>' after struct values")
                return StructLiteral(line=ldict.line, column=ldict.column, struct_name="", values=values)

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

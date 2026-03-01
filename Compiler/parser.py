"""
./Compiler/parser.py
PyPLone Parser
Converts token stream into AST
"""

from lexer import Token, TokenType
from ast_nodes import *
from typing import Optional


class ParseError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[Line {line}:{col}] ParseError: {msg}")
        self.line = line
        self.col = col


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = [
            t
            for t in tokens
            if t.type
            not in (
                TokenType.NEWLINE,
                TokenType.INDENT,
                TokenType.DEDENT,
                TokenType.EOF,
            )
        ]
        self.raw_tokens = tokens  # keep all for block parsing
        self.pos = 0
        self._rebuild_with_structure()

    def _rebuild_with_structure(self):
        """Use raw tokens to preserve indentation structure."""
        self.tokens = self.raw_tokens
        self.pos = 0

    def peek(self, offset=0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, "", 0, 0)

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, *types: TokenType) -> bool:
        return self.peek().type in types

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None

    def expect(self, ttype: TokenType, msg: str = None) -> Token:
        tok = self.peek()
        if tok.type != ttype:
            raise ParseError(
                msg or f"Expected {ttype.name}, got {tok.type.name} ({tok.value!r})",
                tok.line,
                tok.col,
            )
        return self.advance()

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE):
            self.advance()

    def skip_in_brackets(self):
        """Skip newlines, indents, and dedents inside bracket contexts."""
        while self.check(TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            self.advance()

    def error(self, msg=None):
        tok = self.peek()
        raise ParseError(
            msg or f"Unexpected token {tok.type.name} ({tok.value!r})",
            tok.line,
            tok.col,
        )

    # ─── Entry point ─────────────────────────────────────────────────────────

    def parse(self) -> Module:
        self.skip_newlines()
        body = []
        while not self.check(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt is not None:
                body.append(stmt)
            self.skip_newlines()
        return Module(body=body)

    # ─── Statements ──────────────────────────────────────────────────────────

    def parse_stmt(self):
        self.skip_newlines()
        tok = self.peek()

        if tok.type == TokenType.EOF:
            return None

        if tok.type == TokenType.DEF:
            return self.parse_funcdef()
        if tok.type == TokenType.ASYNC and self.peek(1).type == TokenType.DEF:
            return self.parse_funcdef(is_async=True)
        if tok.type == TokenType.CLASS:
            return self.parse_classdef()
        if tok.type == TokenType.RETURN:
            return self.parse_return()
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.WHILE:
            return self.parse_while()
        if tok.type == TokenType.FOR:
            return self.parse_for()
        if tok.type == TokenType.BREAK:
            self.advance()
            self.match(TokenType.NEWLINE)
            return Break(line=tok.line, col=tok.col)
        if tok.type == TokenType.CONTINUE:
            self.advance()
            self.match(TokenType.NEWLINE)
            return Continue(line=tok.line, col=tok.col)
        if tok.type == TokenType.PASS:
            self.advance()
            self.match(TokenType.NEWLINE)
            return Pass(line=tok.line, col=tok.col)
        if tok.type == TokenType.IMPORT or tok.type == TokenType.GET:
            return self.parse_import()
        if tok.type == TokenType.FROM:
            return self.parse_import_from()
        if tok.type == TokenType.TRY:
            return self.parse_try()
        if tok.type == TokenType.RAISE:
            return self.parse_raise()
        if tok.type == TokenType.ASSERT:
            return self.parse_assert()
        if tok.type == TokenType.DEL:
            return self.parse_del()
        if tok.type == TokenType.GLOBAL:
            return self.parse_global()
        if tok.type == TokenType.NONLOCAL:
            return self.parse_nonlocal()
        if tok.type == TokenType.WITH:
            return self.parse_with()
        if tok.type == TokenType.AT:
            return self.parse_decorated()
        if tok.type == TokenType.DELETE_PTR:
            return self.parse_delete_ptr()
        if tok.type == TokenType.PRINT:
            return self.parse_print()
        if tok.type in (TokenType.INDENT, TokenType.DEDENT, TokenType.NEWLINE):
            self.advance()
            return None

        return self.parse_expr_stmt()

    def parse_block(self) -> list:
        """Parse an indented block of statements."""
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        stmts = []
        while not self.check(TokenType.DEDENT) and not self.check(TokenType.EOF):
            stmt = self.parse_stmt()
            if stmt is not None:
                stmts.append(stmt)
        self.match(TokenType.DEDENT)
        return stmts

    def parse_funcdef(self, is_async=False) -> FunctionDef:
        if is_async:
            self.advance()  # async
        tok = self.advance()  # def
        name_tok = self.expect(TokenType.IDENT, "Expected function name")
        self.expect(TokenType.LPAREN)
        params = self.parse_params()
        self.expect(TokenType.RPAREN)

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type_annotation()

        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        return FunctionDef(
            name=name_tok.value,
            params=params,
            body=body,
            return_type=return_type,
            is_async=is_async,
            line=tok.line,
            col=tok.col,
        )

    def parse_params(self) -> list:
        params = []
        if self.check(TokenType.RPAREN):
            return params
        while True:
            tok = self.peek()
            if tok.type == TokenType.STAR:
                self.advance()
                if self.check(TokenType.STAR):
                    self.advance()
                    name = self.expect(TokenType.IDENT)
                    params.append(
                        Param(name="**" + name.value, line=tok.line, col=tok.col)
                    )
                else:
                    if self.check(TokenType.IDENT):
                        name = self.advance()
                        params.append(
                            Param(name="*" + name.value, line=tok.line, col=tok.col)
                        )
                    else:
                        params.append(Param(name="*", line=tok.line, col=tok.col))
            else:
                is_ptr = False
                if self.check(TokenType.AMPERSAND):
                    self.advance()
                    is_ptr = True
                name = self.expect(TokenType.IDENT)
                annotation = None
                if self.match(TokenType.COLON):
                    annotation = self.parse_type_annotation()
                default = None
                if self.match(TokenType.EQ):
                    default = self.parse_expr()
                params.append(
                    Param(
                        name=name.value,
                        annotation=annotation,
                        default=default,
                        is_pointer=is_ptr,
                        line=name.line,
                        col=name.col,
                    )
                )
            if not self.match(TokenType.COMMA):
                break
        return params

    def parse_type_annotation(self):
        """Parse type annotations including ptr<T>."""
        tok = self.peek()
        if tok.type == TokenType.PTR:
            self.advance()
            if self.check(TokenType.LBRACKET):
                self.advance()
                inner = self.parse_type_annotation()
                self.expect(TokenType.RBRACKET)
            else:
                self.expect(TokenType.LT)
                inner = self.parse_type_annotation()
                self.expect(TokenType.GT)
            return PtrType(inner=inner, line=tok.line, col=tok.col)
        elif tok.type in (
            TokenType.INT_T,
            TokenType.FLOAT_T,
            TokenType.STR_T,
            TokenType.BOOL_T,
            TokenType.VOID_T,
            TokenType.AUTO_T,
            TokenType.LIST_T,
            TokenType.DICT_T,
            TokenType.TUPLE_T,
            TokenType.SET_T,
        ):
            self.advance()
            return Name(id=tok.value, line=tok.line, col=tok.col)
        elif tok.type == TokenType.IDENT:
            self.advance()
            return Name(id=tok.value, line=tok.line, col=tok.col)
        else:
            return self.parse_expr()

    def parse_classdef(self) -> ClassDef:
        tok = self.advance()  # class
        name = self.expect(TokenType.IDENT)
        bases = []
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                bases.append(self.parse_expr())
                while self.match(TokenType.COMMA):
                    bases.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        return ClassDef(
            name=name.value, bases=bases, body=body, line=tok.line, col=tok.col
        )

    def parse_return(self) -> Return:
        tok = self.advance()
        value = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            value = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return Return(value=value, line=tok.line, col=tok.col)

    def parse_if(self) -> If:
        tok = self.advance()  # if
        test = self.parse_expr()
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        orelse = []
        self.skip_newlines()
        if self.check(TokenType.ELIF):
            orelse = [self.parse_elif()]
        elif self.check(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON)
            self.match(TokenType.NEWLINE)
            orelse = self.parse_block()
        return If(test=test, body=body, orelse=orelse, line=tok.line, col=tok.col)

    def parse_elif(self) -> If:
        tok = self.advance()  # elif
        test = self.parse_expr()
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        orelse = []
        self.skip_newlines()
        if self.check(TokenType.ELIF):
            orelse = [self.parse_elif()]
        elif self.check(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON)
            self.match(TokenType.NEWLINE)
            orelse = self.parse_block()
        return If(test=test, body=body, orelse=orelse, line=tok.line, col=tok.col)

    def parse_while(self) -> While:
        tok = self.advance()
        test = self.parse_expr()
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        return While(test=test, body=body, line=tok.line, col=tok.col)

    def parse_for(self) -> For:
        tok = self.advance()
        target = self.parse_postfix()
        if self.check(TokenType.COMMA):
            elts = [target]
            while self.match(TokenType.COMMA):
                if self.check(TokenType.IN):
                    break
                elts.append(self.parse_postfix())
            target = Tuple(elts=elts)
        self.expect(TokenType.IN)
        iter_ = self.parse_expr()
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        return For(target=target, iter=iter_, body=body, line=tok.line, col=tok.col)

    def parse_import(self) -> Import:
        tok = self.advance()  # import or get
        names = []
        name = self.expect(TokenType.IDENT).value
        alias = None
        if self.match(TokenType.AS):
            alias = self.expect(TokenType.IDENT).value
        names.append((name, alias))
        while self.match(TokenType.COMMA):
            name = self.expect(TokenType.IDENT).value
            alias = None
            if self.match(TokenType.AS):
                alias = self.expect(TokenType.IDENT).value
            names.append((name, alias))
        self.match(TokenType.NEWLINE)
        return Import(names=names, line=tok.line, col=tok.col)

    def parse_import_from(self) -> ImportFrom:
        tok = self.advance()
        module_parts = [self.expect(TokenType.IDENT).value]
        while self.check(TokenType.DOT):
            self.advance()
            module_parts.append(self.expect(TokenType.IDENT).value)
        module = ".".join(module_parts)
        if not self.match(TokenType.IMPORT):
            self.expect(TokenType.GET)  # from X get Y
        names = []
        if self.match(TokenType.STAR):
            names = [("*", None)]
        else:
            paren = self.match(TokenType.LPAREN)
            name = self.expect(TokenType.IDENT).value
            alias = None
            if self.match(TokenType.AS):
                alias = self.expect(TokenType.IDENT).value
            names.append((name, alias))
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RPAREN):
                    break
                name = self.expect(TokenType.IDENT).value
                alias = None
                if self.match(TokenType.AS):
                    alias = self.expect(TokenType.IDENT).value
                names.append((name, alias))
            if paren:
                self.expect(TokenType.RPAREN)
        self.match(TokenType.NEWLINE)
        return ImportFrom(module=module, names=names, line=tok.line, col=tok.col)

    def parse_try(self) -> Try:
        tok = self.advance()
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        handlers = []
        orelse = []
        finalbody = []
        self.skip_newlines()
        while self.check(TokenType.EXCEPT):
            self.advance()
            exc_type = None
            name = None
            if not self.check(TokenType.COLON):
                exc_type = self.parse_expr()
                if self.match(TokenType.AS):
                    name = self.expect(TokenType.IDENT).value
            self.expect(TokenType.COLON)
            self.match(TokenType.NEWLINE)
            hbody = self.parse_block()
            handlers.append(ExceptHandler(exc_type=exc_type, name=name, body=hbody))
            self.skip_newlines()
        if self.check(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON)
            self.match(TokenType.NEWLINE)
            orelse = self.parse_block()
            self.skip_newlines()
        if self.check(TokenType.FINALLY):
            self.advance()
            self.expect(TokenType.COLON)
            self.match(TokenType.NEWLINE)
            finalbody = self.parse_block()
        return Try(
            body=body,
            handlers=handlers,
            orelse=orelse,
            finalbody=finalbody,
            line=tok.line,
            col=tok.col,
        )

    def parse_raise(self) -> Raise:
        tok = self.advance()
        exc = None
        cause = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            exc = self.parse_expr()
            if self.peek().type == TokenType.IDENT and self.peek().value == "from":
                self.advance()
                cause = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return Raise(exc=exc, cause=cause, line=tok.line, col=tok.col)

    def parse_assert(self) -> Assert:
        tok = self.advance()
        test = self.parse_expr()
        msg = None
        if self.match(TokenType.COMMA):
            msg = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return Assert(test=test, msg=msg, line=tok.line, col=tok.col)

    def parse_del(self) -> Delete:
        tok = self.advance()
        targets = [self.parse_expr()]
        while self.match(TokenType.COMMA):
            targets.append(self.parse_expr())
        self.match(TokenType.NEWLINE)
        return Delete(targets=targets, line=tok.line, col=tok.col)

    def parse_global(self) -> Global:
        tok = self.advance()
        names = [self.expect(TokenType.IDENT).value]
        while self.match(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENT).value)
        self.match(TokenType.NEWLINE)
        return Global(names=names, line=tok.line, col=tok.col)

    def parse_nonlocal(self) -> Nonlocal:
        tok = self.advance()
        names = [self.expect(TokenType.IDENT).value]
        while self.match(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENT).value)
        self.match(TokenType.NEWLINE)
        return Nonlocal(names=names, line=tok.line, col=tok.col)

    def parse_with(self) -> With:
        tok = self.advance()
        items = []
        ctx = self.parse_expr()
        var = None
        if self.match(TokenType.AS):
            var = self.parse_expr()
        items.append((ctx, var))
        while self.match(TokenType.COMMA):
            ctx = self.parse_expr()
            var = None
            if self.match(TokenType.AS):
                var = self.parse_expr()
            items.append((ctx, var))
        self.expect(TokenType.COLON)
        self.match(TokenType.NEWLINE)
        body = self.parse_block()
        return With(items=items, body=body, line=tok.line, col=tok.col)

    def parse_delete_ptr(self) -> DeletePtr:
        tok = self.advance()
        target = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return DeletePtr(target=target, line=tok.line, col=tok.col)

    def parse_print(self) -> PrintStmt:
        tok = self.advance()
        self.expect(TokenType.LPAREN)
        args = []
        end = None
        sep = None
        if not self.check(TokenType.RPAREN):
            # Check for keyword args
            while True:
                if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.EQ:
                    kw = self.advance().value
                    self.advance()  # =
                    val = self.parse_expr()
                    if kw == "end":
                        end = val
                    elif kw == "sep":
                        sep = val
                else:
                    args.append(self.parse_expr())
                if not self.match(TokenType.COMMA):
                    break
                if self.check(TokenType.RPAREN):
                    break
        self.expect(TokenType.RPAREN)
        self.match(TokenType.NEWLINE)
        return PrintStmt(args=args, end=end, sep=sep, line=tok.line, col=tok.col)

    def parse_decorated(self):
        self.advance()  # @
        decorator = self.parse_expr()
        self.match(TokenType.NEWLINE)
        self.skip_newlines()
        if self.check(TokenType.DEF):
            node = self.parse_funcdef()
            node.decorators.insert(0, decorator)
            return node
        elif self.check(TokenType.CLASS):
            node = self.parse_classdef()
            node.decorators.insert(0, decorator)
            return node
        else:
            self.error("Expected def or class after decorator")

    def _parse_tuple_or_expr(self):
        """Parse an expression that might be a comma-separated tuple."""
        expr = self.parse_expr()
        if self.check(TokenType.COMMA):
            elts = [expr]
            while self.match(TokenType.COMMA):
                if (
                    self.check(TokenType.NEWLINE)
                    or self.check(TokenType.EOF)
                    or self.check(TokenType.RBRACKET)
                    or self.check(TokenType.RPAREN)
                ):
                    break
                elts.append(self.parse_expr())
            return Tuple(
                elts=elts, line=getattr(expr, "line", 0), col=getattr(expr, "col", 0)
            )
        return expr

    def parse_expr_stmt(self):
        tok = self.peek()
        expr = self.parse_expr()

        # Tuple expression (a, b = ...) — collect comma-separated targets
        if self.check(TokenType.COMMA):
            elts = [expr]
            while self.match(TokenType.COMMA):
                if self.check(TokenType.EQ) or self.peek().type in (
                    TokenType.PLUSEQ,
                    TokenType.MINUSEQ,
                    TokenType.STAREQ,
                    TokenType.SLASHEQ,
                    TokenType.PERCENTEQ,
                    TokenType.NEWLINE,
                    TokenType.EOF,
                    TokenType.COLON,
                ):
                    break
                elts.append(self.parse_expr())
            expr = Tuple(elts=elts, line=tok.line, col=tok.col)

        # Assignment
        if self.check(TokenType.EQ):
            targets = [expr]
            while self.match(TokenType.EQ):
                if self.check(TokenType.EQ):
                    targets.append(self._parse_tuple_or_expr())
                else:
                    value = self._parse_tuple_or_expr()
                    self.match(TokenType.NEWLINE)
                    return Assign(
                        targets=targets, value=value, line=tok.line, col=tok.col
                    )
            value = self._parse_tuple_or_expr()
            self.match(TokenType.NEWLINE)
            return Assign(targets=targets, value=value, line=tok.line, col=tok.col)

        # Augmented assignment
        aug_ops = {
            TokenType.PLUSEQ: "+=",
            TokenType.MINUSEQ: "-=",
            TokenType.STAREQ: "*=",
            TokenType.SLASHEQ: "/=",
            TokenType.PERCENTEQ: "%=",
        }
        if self.peek().type in aug_ops:
            op = aug_ops[self.advance().type]
            value = self.parse_expr()
            self.match(TokenType.NEWLINE)
            return AugAssign(
                target=expr, op=op, value=value, line=tok.line, col=tok.col
            )

        # Annotated assignment
        if self.check(TokenType.COLON):
            self.advance()
            annotation = self.parse_type_annotation()
            value = None
            if self.match(TokenType.EQ):
                value = self.parse_expr()
            self.match(TokenType.NEWLINE)
            return AnnAssign(
                target=expr,
                annotation=annotation,
                value=value,
                line=tok.line,
                col=tok.col,
            )

        self.match(TokenType.NEWLINE)
        return Expr(value=expr, line=tok.line, col=tok.col)

    # ─── Expressions ─────────────────────────────────────────────────────────

    def parse_expr(self):
        return self.parse_walrus()

    def parse_walrus(self):
        expr = self.parse_lambda()
        if self.check(TokenType.WALRUS):
            tok = self.advance()
            value = self.parse_lambda()
            return WalrusOp(target=expr, value=value, line=tok.line, col=tok.col)
        return expr

    def parse_lambda(self):
        if self.check(TokenType.LAMBDA):
            tok = self.advance()
            params = []
            if not self.check(TokenType.COLON):
                params = self.parse_params()
            self.expect(TokenType.COLON)
            body = self.parse_expr()
            return Lambda(params=params, body=body, line=tok.line, col=tok.col)
        return self.parse_ternary()

    def parse_ternary(self):
        expr = self.parse_or()
        if self.check(TokenType.IF):
            tok = self.advance()
            test = self.parse_or()
            self.expect(TokenType.ELSE)
            orelse = self.parse_ternary()
            return IfExp(
                test=test, body=expr, orelse=orelse, line=tok.line, col=tok.col
            )
        return expr

    def parse_or(self):
        left = self.parse_and()
        while self.check(TokenType.OR):
            tok = self.advance()
            right = self.parse_and()
            if isinstance(left, BoolOp) and left.op == "or":
                left.values.append(right)
            else:
                left = BoolOp(op="or", values=[left, right], line=tok.line, col=tok.col)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.check(TokenType.AND):
            tok = self.advance()
            right = self.parse_not()
            if isinstance(left, BoolOp) and left.op == "and":
                left.values.append(right)
            else:
                left = BoolOp(
                    op="and", values=[left, right], line=tok.line, col=tok.col
                )
        return left

    def parse_not(self):
        if self.check(TokenType.NOT):
            tok = self.advance()
            return UnaryOp(
                op="not", operand=self.parse_not(), line=tok.line, col=tok.col
            )
        return self.parse_compare()

    def parse_compare(self):
        left = self.parse_bitor()
        ops = []
        comps = []
        cmp_types = {
            TokenType.EQEQ: "==",
            TokenType.NEQ: "!=",
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.LTE: "<=",
            TokenType.GTE: ">=",
            TokenType.IS: "is",
            TokenType.IN: "in",
        }
        while self.peek().type in cmp_types or (
            self.peek().type == TokenType.NOT and self.peek(1).type == TokenType.IN
        ):
            if self.peek().type == TokenType.NOT:
                self.advance()
                self.expect(TokenType.IN)
                ops.append("not in")
            elif (
                self.peek().type == TokenType.IS and self.peek(1).type == TokenType.NOT
            ):
                self.advance()
                self.advance()
                ops.append("is not")
            else:
                ops.append(cmp_types[self.advance().type])
            comps.append(self.parse_bitor())
        if ops:
            return Compare(
                left=left,
                ops=ops,
                comparators=comps,
                line=left.line if hasattr(left, "line") else 0,
            )
        return left

    def parse_bitor(self):
        left = self.parse_bitxor()
        while self.check(TokenType.PIPE):
            tok = self.advance()
            right = self.parse_bitxor()
            left = BinOp(left=left, op="|", right=right, line=tok.line, col=tok.col)
        return left

    def parse_bitxor(self):
        left = self.parse_bitand()
        while self.check(TokenType.CARET):
            tok = self.advance()
            right = self.parse_bitand()
            left = BinOp(left=left, op="^", right=right, line=tok.line, col=tok.col)
        return left

    def parse_bitand(self):
        left = self.parse_shift()
        while self.check(TokenType.AMPERSAND):
            tok = self.advance()
            right = self.parse_shift()
            left = BinOp(left=left, op="&", right=right, line=tok.line, col=tok.col)
        return left

    def parse_shift(self):
        left = self.parse_add()
        while self.check(TokenType.LSHIFT, TokenType.RSHIFT):
            tok = self.advance()
            right = self.parse_add()
            left = BinOp(
                left=left, op=tok.value, right=right, line=tok.line, col=tok.col
            )
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            tok = self.advance()
            right = self.parse_mul()
            left = BinOp(
                left=left, op=tok.value, right=right, line=tok.line, col=tok.col
            )
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.check(
            TokenType.STAR, TokenType.SLASH, TokenType.DOUBLESLASH, TokenType.PERCENT
        ):
            tok = self.advance()
            right = self.parse_unary()
            left = BinOp(
                left=left, op=tok.value, right=right, line=tok.line, col=tok.col
            )
        return left

    def parse_unary(self):
        if self.check(TokenType.MINUS):
            tok = self.advance()
            return UnaryOp(
                op="-", operand=self.parse_unary(), line=tok.line, col=tok.col
            )
        if self.check(TokenType.PLUS):
            tok = self.advance()
            return UnaryOp(
                op="+", operand=self.parse_unary(), line=tok.line, col=tok.col
            )
        if self.check(TokenType.TILDE):
            tok = self.advance()
            return UnaryOp(
                op="~", operand=self.parse_unary(), line=tok.line, col=tok.col
            )
        # Pointer dereference: *expr
        if self.check(TokenType.STAR):
            tok = self.advance()
            return Deref(operand=self.parse_unary(), line=tok.line, col=tok.col)
        # Address-of: &expr
        if self.check(TokenType.AMPERSAND):
            tok = self.advance()
            return AddressOf(operand=self.parse_unary(), line=tok.line, col=tok.col)
        return self.parse_power()

    def parse_power(self):
        left = self.parse_postfix()
        if self.check(TokenType.DOUBLESTAR):
            tok = self.advance()
            right = self.parse_unary()
            return BinOp(left=left, op="**", right=right, line=tok.line, col=tok.col)
        return left

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.check(TokenType.DOT):
                tok = self.advance()
                # Allow keyword identifiers as attribute names (e.g. obj.get(), obj.get)
                attr_tok = self.peek()
                keyword_as_attr = {
                    TokenType.GET,
                    TokenType.IMPORT,
                    TokenType.FROM,
                    TokenType.IN,
                    TokenType.IS,
                    TokenType.NOT,
                    TokenType.AND,
                    TokenType.OR,
                    TokenType.NEW,
                    TokenType.DELETE_PTR,
                    TokenType.INT_T,
                    TokenType.FLOAT_T,
                    TokenType.STR_T,
                    TokenType.BOOL_T,
                    TokenType.LIST_T,
                    TokenType.DICT_T,
                    TokenType.SET_T,
                    TokenType.TUPLE_T,
                    TokenType.AUTO_T,
                    TokenType.PTR,
                }
                if attr_tok.type in keyword_as_attr or attr_tok.type == TokenType.IDENT:
                    attr = self.advance()
                    expr = Attribute(
                        obj=expr, attr=attr.value, line=tok.line, col=tok.col
                    )
                else:
                    self.error(f"Expected attribute name, got {attr_tok.type.name}")
            elif self.check(TokenType.ARROW):
                tok = self.advance()
                attr = self.expect(TokenType.IDENT)
                expr = Attribute(
                    obj=expr,
                    attr=attr.value,
                    is_ptr_access=True,
                    line=tok.line,
                    col=tok.col,
                )
            elif self.check(TokenType.LBRACKET):
                tok = self.advance()
                idx = self.parse_slice_or_expr()
                self.expect(TokenType.RBRACKET)
                expr = Subscript(obj=expr, index=idx, line=tok.line, col=tok.col)
            elif self.check(TokenType.LPAREN):
                tok = self.advance()
                args, kwargs = self.parse_call_args()
                self.expect(TokenType.RPAREN)
                expr = Call(
                    func=expr, args=args, kwargs=kwargs, line=tok.line, col=tok.col
                )
            else:
                break
        return expr

    def parse_slice_or_expr(self):
        if self.check(TokenType.COLON):
            lower = None
        else:
            lower = self.parse_expr()
        if not self.check(TokenType.COLON):
            return lower
        self.advance()
        upper = None
        if not self.check(TokenType.RBRACKET) and not self.check(TokenType.COLON):
            upper = self.parse_expr()
        step = None
        if self.check(TokenType.COLON):
            self.advance()
            if not self.check(TokenType.RBRACKET):
                step = self.parse_expr()
        return Slice(lower=lower, upper=upper, step=step)

    def parse_call_args(self):
        args = []
        kwargs = []
        self.skip_in_brackets()
        if self.check(TokenType.RPAREN):
            return args, kwargs
        while True:
            if self.check(TokenType.STAR):
                self.advance()
                args.append(Starred(value=self.parse_expr()))
            elif self.check(TokenType.DOUBLESTAR):
                self.advance()
                kwargs.append((None, self.parse_expr()))
            elif self.check(TokenType.IDENT) and self.peek(1).type == TokenType.EQ:
                key = self.advance().value
                self.advance()
                kwargs.append((key, self.parse_expr()))
            else:
                expr = self.parse_expr()
                # Generator expression inside call: f(x for x in ...)
                if self.check(TokenType.FOR):
                    gens = self.parse_comprehension_for()
                    expr = GeneratorExp(
                        elt=expr,
                        generators=gens,
                        line=getattr(expr, "line", 0),
                        col=getattr(expr, "col", 0),
                    )
                args.append(expr)
            if not self.match(TokenType.COMMA):
                break
            self.skip_in_brackets()
            if self.check(TokenType.RPAREN):
                break
        return args, kwargs

    def parse_primary(self):
        tok = self.peek()

        # Literals
        if tok.type == TokenType.INTEGER:
            self.advance()
            return Const(
                value=int(tok.value.replace("_", ""), 0), line=tok.line, col=tok.col
            )
        if tok.type == TokenType.FLOAT:
            self.advance()
            return Const(
                value=float(tok.value.replace("_", "")), line=tok.line, col=tok.col
            )
        if tok.type == TokenType.STRING:
            self.advance()
            return Const(value=tok.value, line=tok.line, col=tok.col)
        if tok.type == TokenType.BOOL:
            self.advance()
            return Const(value=tok.value == "True", line=tok.line, col=tok.col)
        if tok.type == TokenType.NONE:
            self.advance()
            return Const(value=None, line=tok.line, col=tok.col)
        if tok.type == TokenType.NULLPTR:
            self.advance()
            return NullPtr(line=tok.line, col=tok.col)

        # new keyword
        if tok.type == TokenType.NEW:
            self.advance()
            type_tok = self.peek()
            type_name_types = (
                TokenType.IDENT,
                TokenType.INT_T,
                TokenType.FLOAT_T,
                TokenType.STR_T,
                TokenType.BOOL_T,
                TokenType.LIST_T,
                TokenType.DICT_T,
                TokenType.SET_T,
                TokenType.TUPLE_T,
            )
            if type_tok.type not in type_name_types:
                self.error("Expected type name after new")
            type_name = self.advance().value
            self.expect(TokenType.LPAREN)
            args, _ = self.parse_call_args()
            self.expect(TokenType.RPAREN)
            return NewExpr(type_name=type_name, args=args, line=tok.line, col=tok.col)

        # Yield / Await
        if tok.type == TokenType.YIELD:
            self.advance()
            value = None
            if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
                value = self.parse_expr()
            return Yield(value=value, line=tok.line, col=tok.col)
        if tok.type == TokenType.AWAIT:
            self.advance()
            return Await(value=self.parse_unary(), line=tok.line, col=tok.col)

        # Names
        if tok.type == TokenType.IDENT:
            self.advance()
            return Name(id=tok.value, line=tok.line, col=tok.col)

        # Type names used as values
        if tok.type in (
            TokenType.INT_T,
            TokenType.FLOAT_T,
            TokenType.STR_T,
            TokenType.BOOL_T,
            TokenType.LIST_T,
            TokenType.DICT_T,
            TokenType.SET_T,
            TokenType.TUPLE_T,
        ):
            self.advance()
            return Name(id=tok.value, line=tok.line, col=tok.col)

        # Parenthesized expression or tuple
        if tok.type == TokenType.LPAREN:
            self.advance()
            self.skip_in_brackets()
            if self.check(TokenType.RPAREN):
                self.advance()
                return Tuple(elts=[], line=tok.line, col=tok.col)
            expr = self.parse_expr()
            self.skip_in_brackets()
            if self.check(TokenType.COMMA):
                elts = [expr]
                while self.match(TokenType.COMMA):
                    self.skip_in_brackets()
                    if self.check(TokenType.RPAREN):
                        break
                    elts.append(self.parse_expr())
                    self.skip_in_brackets()
                self.expect(TokenType.RPAREN)
                return Tuple(elts=elts, line=tok.line, col=tok.col)
            # Generator expression
            if self.check(TokenType.FOR):
                gens = self.parse_comprehension_for()
                self.skip_in_brackets()
                self.expect(TokenType.RPAREN)
                return GeneratorExp(
                    elt=expr, generators=gens, line=tok.line, col=tok.col
                )
            self.expect(TokenType.RPAREN)
            return expr

        # List
        if tok.type == TokenType.LBRACKET:
            self.advance()
            self.skip_in_brackets()
            if self.check(TokenType.RBRACKET):
                self.advance()
                return List(elts=[], line=tok.line, col=tok.col)
            expr = self.parse_expr()
            self.skip_in_brackets()
            if self.check(TokenType.FOR):
                gens = self.parse_comprehension_for()
                self.skip_in_brackets()
                self.expect(TokenType.RBRACKET)
                return ListComp(elt=expr, generators=gens, line=tok.line, col=tok.col)
            elts = [expr]
            while self.match(TokenType.COMMA):
                self.skip_in_brackets()
                if self.check(TokenType.RBRACKET):
                    break
                elts.append(self.parse_expr())
                self.skip_in_brackets()
            self.expect(TokenType.RBRACKET)
            return List(elts=elts, line=tok.line, col=tok.col)

        # Dict or Set
        if tok.type == TokenType.LBRACE:
            self.advance()
            self.skip_in_brackets()
            if self.check(TokenType.RBRACE):
                self.advance()
                return Dict(keys=[], values=[], line=tok.line, col=tok.col)
            first = self.parse_expr()
            self.skip_in_brackets()
            if self.check(TokenType.COLON):
                # Dict or DictComp
                self.advance()
                self.skip_in_brackets()
                first_val = self.parse_expr()
                self.skip_in_brackets()
                if self.check(TokenType.FOR):
                    gens = self.parse_comprehension_for()
                    self.skip_in_brackets()
                    self.expect(TokenType.RBRACE)
                    return DictComp(
                        key=first,
                        value=first_val,
                        generators=gens,
                        line=tok.line,
                        col=tok.col,
                    )
                keys = [first]
                values = [first_val]
                while self.match(TokenType.COMMA):
                    self.skip_in_brackets()
                    if self.check(TokenType.RBRACE):
                        break
                    k = self.parse_expr()
                    self.skip_in_brackets()
                    self.expect(TokenType.COLON)
                    self.skip_in_brackets()
                    v = self.parse_expr()
                    self.skip_in_brackets()
                    keys.append(k)
                    values.append(v)
                self.expect(TokenType.RBRACE)
                return Dict(keys=keys, values=values, line=tok.line, col=tok.col)
            else:
                # Set
                elts = [first]
                while self.match(TokenType.COMMA):
                    self.skip_in_brackets()
                    if self.check(TokenType.RBRACE):
                        break
                    elts.append(self.parse_expr())
                    self.skip_in_brackets()
                self.expect(TokenType.RBRACE)
                return Set(elts=elts, line=tok.line, col=tok.col)

        # Star expression
        if tok.type == TokenType.STAR:
            self.advance()
            return Starred(value=self.parse_expr(), line=tok.line, col=tok.col)

        self.error(f"Unexpected token in expression: {tok.type.name} ({tok.value!r})")

    def parse_comprehension_for(self) -> list:
        gens = []
        while self.check(TokenType.FOR):
            self.advance()
            # Parse target(s) — stop before 'in'
            target = self.parse_postfix()
            if self.check(TokenType.COMMA):
                elts = [target]
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.IN):
                        break
                    elts.append(self.parse_postfix())
                target = Tuple(elts=elts)
            self.expect(TokenType.IN)
            iter_ = self.parse_or()
            ifs = []
            while self.check(TokenType.IF):
                self.advance()
                ifs.append(self.parse_or())
            gens.append(Comprehension(target=target, iter=iter_, ifs=ifs))
        return gens

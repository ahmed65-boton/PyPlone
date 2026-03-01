"""
PyPLone Lexer - Tokenizes .pylo source files
PyPLone: Python-like syntax with C++ pointer support
./Compiler/lexer.py
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    NONE = auto()

    # Identifiers & Keywords
    IDENT = auto()
    DEF = auto()
    CLASS = auto()
    RETURN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    BREAK = auto()
    CONTINUE = auto()
    PASS = auto()
    IMPORT = auto()
    FROM = auto()
    GET = auto()  # 'get' keyword (alias for import)
    AS = auto()
    TRY = auto()
    EXCEPT = auto()
    FINALLY = auto()
    RAISE = auto()
    WITH = auto()
    LAMBDA = auto()
    YIELD = auto()
    ASYNC = auto()
    AWAIT = auto()
    GLOBAL = auto()
    NONLOCAL = auto()
    DEL = auto()
    ASSERT = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IS = auto()
    IN_KW = auto()
    PRINT = auto()

    # Pointer keywords (C++ style)
    PTR = auto()  # ptr<T>  - pointer type annotation
    DEREF = auto()  # *x      - dereference (prefix)
    ADDR = auto()  # &x      - address-of
    NULLPTR = auto()  # nullptr
    NEW = auto()  # new
    DELETE_PTR = auto()  # delete  - free pointer

    # Type annotations
    INT_T = auto()
    FLOAT_T = auto()
    STR_T = auto()
    BOOL_T = auto()
    LIST_T = auto()
    DICT_T = auto()
    TUPLE_T = auto()
    SET_T = auto()
    VOID_T = auto()
    AUTO_T = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    DOUBLESLASH = auto()
    PERCENT = auto()
    DOUBLESTAR = auto()
    EQ = auto()
    PLUSEQ = auto()
    MINUSEQ = auto()
    STAREQ = auto()
    SLASHEQ = auto()
    PERCENTEQ = auto()
    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    TILDE = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    ARROW = auto()  # ->  (pointer member access)
    WALRUS = auto()  # :=

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()
    AT = auto()
    HASH = auto()

    # Structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "def": TokenType.DEF,
    "class": TokenType.CLASS,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "pass": TokenType.PASS,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "get": TokenType.GET,  # PyPLone alias for import
    "as": TokenType.AS,
    "try": TokenType.TRY,
    "except": TokenType.EXCEPT,
    "finally": TokenType.FINALLY,
    "raise": TokenType.RAISE,
    "with": TokenType.WITH,
    "lambda": TokenType.LAMBDA,
    "yield": TokenType.YIELD,
    "async": TokenType.ASYNC,
    "await": TokenType.AWAIT,
    "global": TokenType.GLOBAL,
    "nonlocal": TokenType.NONLOCAL,
    "del": TokenType.DEL,
    "assert": TokenType.ASSERT,
    "not": TokenType.NOT,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "is": TokenType.IS,
    "True": TokenType.BOOL,
    "False": TokenType.BOOL,
    "None": TokenType.NONE,
    "print": TokenType.PRINT,
    # Pointer keywords
    "ptr": TokenType.PTR,
    "nullptr": TokenType.NULLPTR,
    "new": TokenType.NEW,
    "delete": TokenType.DELETE_PTR,
    # Type keywords
    "int": TokenType.INT_T,
    "float": TokenType.FLOAT_T,
    "str": TokenType.STR_T,
    "bool": TokenType.BOOL_T,
    "list": TokenType.LIST_T,
    "dict": TokenType.DICT_T,
    "tuple": TokenType.TUPLE_T,
    "set": TokenType.SET_T,
    "void": TokenType.VOID_T,
    "auto": TokenType.AUTO_T,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[Line {line}:{col}] LexerError: {msg}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.indent_stack = [0]

    def error(self, msg):
        raise LexerError(msg, self.line, self.col)

    def peek(self, offset=0) -> Optional[str]:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.advance()
            return True
        return False

    def add(self, ttype: TokenType, value: str):
        self.tokens.append(Token(ttype, value, self.line, self.col))

    def skip_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self.pos += 1
            self.col += 1

    def read_string(self, quote: str) -> str:
        """Read a string literal (handles triple quotes too)."""
        triple = False
        if self.peek() == quote and self.peek(1) == quote:
            triple = True
            self.advance()
            self.advance()

        result = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch is None:
                self.error("Unterminated string literal")
            if triple:
                if ch == quote and self.peek(1) == quote and self.peek(2) == quote:
                    self.advance()
                    self.advance()
                    self.advance()
                    break
            else:
                if ch == quote:
                    self.advance()
                    break
                if ch == "\n":
                    self.error("Unterminated string literal")
            if ch == "\\":
                self.advance()
                esc = self.advance()
                escapes = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                    "0": "\0",
                }
                result.append(escapes.get(esc, "\\" + esc))
            else:
                result.append(self.advance())
        return "".join(result)

    def read_number(self, first: str) -> Token:
        num = [first]
        is_float = False
        line, col = self.line, self.col

        # Hex
        if first == "0" and self.peek() in ("x", "X"):
            num.append(self.advance())
            while self.peek() and (
                self.peek().isdigit() or self.peek() in "abcdefABCDEF_"
            ):
                num.append(self.advance())
            return Token(TokenType.INTEGER, "".join(num), line, col)

        while self.peek() and (self.peek().isdigit() or self.peek() == "_"):
            num.append(self.advance())

        if self.peek() == "." and self.peek(1) and self.peek(1).isdigit():
            is_float = True
            num.append(self.advance())
            while self.peek() and (self.peek().isdigit() or self.peek() == "_"):
                num.append(self.advance())

        if self.peek() in ("e", "E"):
            is_float = True
            num.append(self.advance())
            if self.peek() in ("+", "-"):
                num.append(self.advance())
            while self.peek() and self.peek().isdigit():
                num.append(self.advance())

        val = "".join(num)
        ttype = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(ttype, val, line, col)

    def handle_indent(self, indent_level: int):
        current = self.indent_stack[-1]
        if indent_level > current:
            self.indent_stack.append(indent_level)
            self.add(TokenType.INDENT, "")
        elif indent_level < current:
            while self.indent_stack[-1] > indent_level:
                self.indent_stack.pop()
                self.add(TokenType.DEDENT, "")
            if self.indent_stack[-1] != indent_level:
                self.error(f"Indentation error: unexpected indent level {indent_level}")

    def tokenize(self) -> list[Token]:
        source_lines = self.source.split("\n")
        # Reset
        self.pos = 0
        self.line = 1
        self.col = 1

        at_line_start = True
        indent_level = 0
        bracket_depth = 0

        while self.pos < len(self.source):
            ch = self.peek()
            start_line = self.line
            start_col = self.col

            # Handle indentation at line start
            if at_line_start and bracket_depth > 0:
                while self.peek() in (" ", "\t"):
                    self.advance()
                at_line_start = False
                continue
            if at_line_start:
                spaces = 0
                while self.peek() in (" ", "\t"):
                    if self.peek() == "\t":
                        spaces += 4
                    else:
                        spaces += 1
                    self.advance()

                # Skip blank lines and comment-only lines
                if self.peek() == "\n":
                    self.advance()
                    continue
                if self.peek() == "#":
                    self.skip_comment()
                    if self.peek() == "\n":
                        self.advance()
                    continue
                if self.peek() is None:
                    break

                self.handle_indent(spaces)
                at_line_start = False
                continue

            ch = self.advance()

            # Whitespace (not newline)
            if ch in (" ", "\t"):
                continue

            # Newline
            if ch == "\n":
                if bracket_depth > 0:
                    at_line_start = False
                    continue
                # Don't emit newline for empty logical lines
                if self.tokens and self.tokens[-1].type not in (
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.DEDENT,
                ):
                    self.tokens.append(
                        Token(TokenType.NEWLINE, "\n", start_line, start_col)
                    )
                at_line_start = True
                continue

            # Comments
            if ch == "#":
                self.skip_comment()
                continue

            # String literals
            if ch in ('"', "'"):
                s = self.read_string(ch)
                self.tokens.append(Token(TokenType.STRING, s, start_line, start_col))
                continue

            # f-strings (basic support)
            if ch == "f" and self.peek() in ('"', "'"):
                q = self.advance()
                s = self.read_string(q)
                self.tokens.append(
                    Token(TokenType.STRING, "f:" + s, start_line, start_col)
                )
                continue

            # Numbers
            if ch.isdigit() or (ch == "." and self.peek() and self.peek().isdigit()):
                tok = self.read_number(ch)
                self.tokens.append(tok)
                continue

            # Identifiers & keywords
            if ch.isalpha() or ch == "_":
                ident = [ch]
                while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
                    ident.append(self.advance())
                word = "".join(ident)
                ttype = KEYWORDS.get(word, TokenType.IDENT)
                self.tokens.append(Token(ttype, word, start_line, start_col))
                continue

            # Operators and punctuation
            if ch == "+":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.PLUSEQ, "+=", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.PLUS, "+", start_line, start_col)
                    )
            elif ch == "-":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.MINUSEQ, "-=", start_line, start_col)
                    )
                elif self.match(">"):
                    self.tokens.append(
                        Token(TokenType.ARROW, "->", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.MINUS, "-", start_line, start_col)
                    )
            elif ch == "*":
                if self.match("*"):
                    self.tokens.append(
                        Token(TokenType.DOUBLESTAR, "**", start_line, start_col)
                    )
                elif self.match("="):
                    self.tokens.append(
                        Token(TokenType.STAREQ, "*=", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.STAR, "*", start_line, start_col)
                    )
            elif ch == "/":
                if self.match("/"):
                    self.tokens.append(
                        Token(TokenType.DOUBLESLASH, "//", start_line, start_col)
                    )
                elif self.match("="):
                    self.tokens.append(
                        Token(TokenType.SLASHEQ, "/=", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.SLASH, "/", start_line, start_col)
                    )
            elif ch == "%":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.PERCENTEQ, "%=", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.PERCENT, "%", start_line, start_col)
                    )
            elif ch == "=":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.EQEQ, "==", start_line, start_col)
                    )
                else:
                    self.tokens.append(Token(TokenType.EQ, "=", start_line, start_col))
            elif ch == "!":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.NEQ, "!=", start_line, start_col)
                    )
                else:
                    self.error(f"Unexpected character '!'")
            elif ch == "<":
                if self.match("<"):
                    self.tokens.append(
                        Token(TokenType.LSHIFT, "<<", start_line, start_col)
                    )
                elif self.match("="):
                    self.tokens.append(
                        Token(TokenType.LTE, "<=", start_line, start_col)
                    )
                else:
                    self.tokens.append(Token(TokenType.LT, "<", start_line, start_col))
            elif ch == ">":
                if self.match(">"):
                    self.tokens.append(
                        Token(TokenType.RSHIFT, ">>", start_line, start_col)
                    )
                elif self.match("="):
                    self.tokens.append(
                        Token(TokenType.GTE, ">=", start_line, start_col)
                    )
                else:
                    self.tokens.append(Token(TokenType.GT, ">", start_line, start_col))
            elif ch == "&":
                self.tokens.append(
                    Token(TokenType.AMPERSAND, "&", start_line, start_col)
                )
            elif ch == "|":
                self.tokens.append(Token(TokenType.PIPE, "|", start_line, start_col))
            elif ch == "^":
                self.tokens.append(Token(TokenType.CARET, "^", start_line, start_col))
            elif ch == "~":
                self.tokens.append(Token(TokenType.TILDE, "~", start_line, start_col))
            elif ch == ":":
                if self.match("="):
                    self.tokens.append(
                        Token(TokenType.WALRUS, ":=", start_line, start_col)
                    )
                else:
                    self.tokens.append(
                        Token(TokenType.COLON, ":", start_line, start_col)
                    )
            elif ch == "(":
                bracket_depth += 1
                self.tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                bracket_depth = max(0, bracket_depth - 1)
                self.tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == "[":
                bracket_depth += 1
                self.tokens.append(
                    Token(TokenType.LBRACKET, "[", start_line, start_col)
                )
            elif ch == "]":
                bracket_depth = max(0, bracket_depth - 1)
                self.tokens.append(
                    Token(TokenType.RBRACKET, "]", start_line, start_col)
                )
            elif ch == "{":
                bracket_depth += 1
                self.tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == "}":
                bracket_depth = max(0, bracket_depth - 1)
                self.tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == ",":
                self.tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == ".":
                self.tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            elif ch == ";":
                self.tokens.append(
                    Token(TokenType.SEMICOLON, ";", start_line, start_col)
                )
            elif ch == "@":
                self.tokens.append(Token(TokenType.AT, "@", start_line, start_col))
            else:
                self.error(f"Unexpected character: {ch!r}")

        # Close any remaining indents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.add(TokenType.DEDENT, "")

        self.add(TokenType.EOF, "")
        return self.tokens

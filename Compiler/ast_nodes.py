# ./Compiler/ast_nodes.py
"""
PyPLone AST Node Definitions
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# ─── Base ────────────────────────────────────────────────────────────────────


@dataclass
class Node:
    line: int = field(default=0, repr=False)
    col: int = field(default=0, repr=False)


# ─── Statements ──────────────────────────────────────────────────────────────


@dataclass
class Module(Node):
    body: list = field(default_factory=list)


@dataclass
class FunctionDef(Node):
    name: str = ""
    params: list = field(default_factory=list)  # list of Param
    body: list = field(default_factory=list)
    return_type: Any = None
    decorators: list = field(default_factory=list)
    is_async: bool = False


@dataclass
class Param(Node):
    name: str = ""
    annotation: Any = None
    default: Any = None
    is_pointer: bool = False


@dataclass
class ClassDef(Node):
    name: str = ""
    bases: list = field(default_factory=list)
    body: list = field(default_factory=list)
    decorators: list = field(default_factory=list)


@dataclass
class Return(Node):
    value: Any = None


@dataclass
class Assign(Node):
    targets: list = field(default_factory=list)
    value: Any = None
    type_annotation: Any = None


@dataclass
class AugAssign(Node):
    target: Any = None
    op: str = ""
    value: Any = None


@dataclass
class AnnAssign(Node):
    target: Any = None
    annotation: Any = None
    value: Any = None


@dataclass
class If(Node):
    test: Any = None
    body: list = field(default_factory=list)
    orelse: list = field(default_factory=list)


@dataclass
class While(Node):
    test: Any = None
    body: list = field(default_factory=list)
    orelse: list = field(default_factory=list)


@dataclass
class For(Node):
    target: Any = None
    iter: Any = None
    body: list = field(default_factory=list)
    orelse: list = field(default_factory=list)


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class Pass(Node):
    pass


@dataclass
class Import(Node):
    names: list = field(default_factory=list)  # list of (name, alias)


@dataclass
class ImportFrom(Node):
    module: str = ""
    names: list = field(default_factory=list)


@dataclass
class Try(Node):
    body: list = field(default_factory=list)
    handlers: list = field(default_factory=list)  # ExceptHandler
    orelse: list = field(default_factory=list)
    finalbody: list = field(default_factory=list)


@dataclass
class ExceptHandler(Node):
    exc_type: Any = None
    name: Optional[str] = None
    body: list = field(default_factory=list)


@dataclass
class Raise(Node):
    exc: Any = None
    cause: Any = None


@dataclass
class Assert(Node):
    test: Any = None
    msg: Any = None


@dataclass
class Delete(Node):
    targets: list = field(default_factory=list)


@dataclass
class Global(Node):
    names: list = field(default_factory=list)


@dataclass
class Nonlocal(Node):
    names: list = field(default_factory=list)


@dataclass
class Expr(Node):
    value: Any = None


@dataclass
class With(Node):
    items: list = field(default_factory=list)  # (ctx_expr, opt_var)
    body: list = field(default_factory=list)


# ─── Pointer Statements ───────────────────────────────────────────────────────


@dataclass
class NewExpr(Node):
    """new Type(args) - heap allocation"""

    type_name: str = ""
    args: list = field(default_factory=list)


@dataclass
class DeletePtr(Node):
    """delete ptr - free heap allocation"""

    target: Any = None


# ─── Expressions ─────────────────────────────────────────────────────────────


@dataclass
class BinOp(Node):
    left: Any = None
    op: str = ""
    right: Any = None


@dataclass
class UnaryOp(Node):
    op: str = ""
    operand: Any = None


@dataclass
class BoolOp(Node):
    op: str = ""  # 'and' or 'or'
    values: list = field(default_factory=list)


@dataclass
class Compare(Node):
    left: Any = None
    ops: list = field(default_factory=list)
    comparators: list = field(default_factory=list)


@dataclass
class Call(Node):
    func: Any = None
    args: list = field(default_factory=list)
    kwargs: list = field(default_factory=list)  # list of (key, value)


@dataclass
class Attribute(Node):
    obj: Any = None
    attr: str = ""
    is_ptr_access: bool = False  # True when using -> instead of .


@dataclass
class Subscript(Node):
    obj: Any = None
    index: Any = None


@dataclass
class Slice(Node):
    lower: Any = None
    upper: Any = None
    step: Any = None


@dataclass
class Name(Node):
    id: str = ""


@dataclass
class Const(Node):
    value: Any = None


@dataclass
class List(Node):
    elts: list = field(default_factory=list)


@dataclass
class Tuple(Node):
    elts: list = field(default_factory=list)


@dataclass
class Dict(Node):
    keys: list = field(default_factory=list)
    values: list = field(default_factory=list)


@dataclass
class Set(Node):
    elts: list = field(default_factory=list)


@dataclass
class ListComp(Node):
    elt: Any = None
    generators: list = field(default_factory=list)


@dataclass
class DictComp(Node):
    key: Any = None
    value: Any = None
    generators: list = field(default_factory=list)


@dataclass
class GeneratorExp(Node):
    elt: Any = None
    generators: list = field(default_factory=list)


@dataclass
class Comprehension(Node):
    target: Any = None
    iter: Any = None
    ifs: list = field(default_factory=list)


@dataclass
class Lambda(Node):
    params: list = field(default_factory=list)
    body: Any = None


@dataclass
class IfExp(Node):
    test: Any = None
    body: Any = None
    orelse: Any = None


@dataclass
class Yield(Node):
    value: Any = None


@dataclass
class Await(Node):
    value: Any = None


@dataclass
class Starred(Node):
    value: Any = None


@dataclass
class WalrusOp(Node):
    target: Any = None
    value: Any = None


@dataclass
class PrintStmt(Node):
    args: list = field(default_factory=list)
    end: Any = None
    sep: Any = None


# ─── Pointer Expressions ──────────────────────────────────────────────────────


@dataclass
class AddressOf(Node):
    """&variable - get pointer to variable"""

    operand: Any = None


@dataclass
class Deref(Node):
    """*pointer - dereference a pointer"""

    operand: Any = None


@dataclass
class PtrType(Node):
    """ptr<T> - pointer type annotation"""

    inner: Any = None


@dataclass
class NullPtr(Node):
    """nullptr literal"""

    pass

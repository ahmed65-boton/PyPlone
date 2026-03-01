# PyPLone Language Reference

**PyPLone** (`.pylo`) is a programming language that combines the clean, readable
syntax of **Python 3.13+** with **C++ pointer semantics** — giving you the best
of both worlds: Python's expressiveness with low-level memory control.

---

## Quick Start

```bash
# Run directly
python pyplone.py hello.pylo --run

# Transpile to Python
python pyplone.py hello.pylo --py

# Compile to standalone .exe (requires PyInstaller)
python pyplone.py hello.pylo
```

---

## Language Features

### Python Features (fully supported)

| Feature | Example |
|---------|---------|
| Type annotations | `x: int = 42` |
| F-strings | `f"Hello, {name}!"` |
| List comprehensions | `[x**2 for x in range(10)]` |
| Dict comprehensions | `{k: v for k, v in items}` |
| Classes & inheritance | `class Dog(Animal):` |
| Decorators | `@property` |
| Lambda | `fn = lambda x: x * 2` |
| Walrus operator | `if n := len(data)` |
| Exception handling | `try/except/finally` |
| Context managers | `with open(f) as fh:` |
| Generators / yield | `yield value` |
| Async / await | `async def fetch():` |
| Match (pattern) | Coming in v1.1 |

### Pointer Features (C++ style)

| Syntax | Meaning | Python equivalent |
|--------|---------|-------------------|
| `ptr[T]` | Pointer-to-T type annotation | `int` (address) |
| `nullptr` | Null pointer | `None` |
| `new T(args)` | Heap-allocate a T | `_heap.alloc(T(args))` |
| `delete p` | Free heap memory | `_heap.free(p)` |
| `&x` | Get address of x | `_heap.addr_of(x)` |
| `*p` | Dereference pointer p | `_heap.deref(p)` |
| `p->field` | Pointer member access | `_heap.deref(p).field` |

---

## Pointer Examples

### Basic Pointer Operations

```pylo
# Declare a pointer-to-int
x: int = 42
p: ptr[int] = &x          # take address

print(*p)                  # dereference: prints 42

y_ptr: ptr[int] = new int(100)   # heap alloc
print(*y_ptr)              # 100
delete y_ptr               # free memory
```

### Linked List

```pylo
class Node:
    def __init__(self, value: int):
        self.value = value
        self.next: ptr[Node] = nullptr

# Allocate a node on the heap
head: ptr[Node] = new Node(10)
second: ptr[Node] = new Node(20)
head->next = second        # -> for pointer member access

print(head->value)         # 10
print(head->next->value)   # 20

delete second
delete head
```

### Pointer to Custom Class

```pylo
class Vec2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

v_ptr: ptr[Vec2] = new Vec2(3.0, 4.0)
length: float = (v_ptr->x ** 2 + v_ptr->y ** 2) ** 0.5
print(f"Length: {length}")   # 5.0
delete v_ptr
```

---

## Type System

PyPLone supports optional type annotations on variables and function signatures.

```pylo
def add(a: int, b: int) -> int:
    return a + b

def process(data: list, callback: auto) -> dict:
    return {i: callback(x) for i, x in enumerate(data)}
```

### Pointer Types

```pylo
def swap(a: ptr[int], b: ptr[int]):
    tmp: int = *a
    *a = *b   # Note: direct deref-assign coming in v1.1
    *b = tmp
```

---

## Compiler Architecture

```
source.pylo
    │
    ▼
┌─────────┐     tokens      ┌─────────┐     AST        ┌──────────┐
│  Lexer  │────────────────▶│ Parser  │───────────────▶│ Codegen  │
│ lexer.py│                 │parser.py│                 │codegen.py│
└─────────┘                 └─────────┘                 └──────────┘
                                                              │
                                                              ▼
                                                       transpiled.py
                                                              │
                                                              ▼
                                                       PyInstaller
                                                              │
                                                              ▼
                                                        output.exe
```

### Components

| File | Role |
|------|------|
| `pyplone.py` | CLI entry point & compilation driver |
| `lexer.py` | Tokenizer — source text → Token stream |
| `parser.py` | Recursive descent parser → AST |
| `ast_nodes.py` | AST node dataclasses |
| `codegen.py` | Code generator — AST → Python source |

### Pointer Runtime

When pointer operations are detected, the compiler automatically injects a
lightweight `_PyPloneHeap` runtime class at the top of the generated Python:

```python
class _PyPloneHeap:
    def alloc(self, obj)       # new T(...)  →  returns address (int)
    def deref(self, addr)      # *p          →  returns object
    def free(self, addr)       # delete p    →  removes from heap
    def addr_of(self, obj)     # &x          →  returns address
    def set(self, addr, value) # write through pointer
```

Safety checks are performed at runtime:
- **Null pointer dereference** → raises `RuntimeError`
- **Use-after-free** → raises `RuntimeError`
- **Double-free** → raises `RuntimeError`
- **Write through null** → raises `RuntimeError`

---

## File Extension

PyPLone source files use the `.pylo` extension.

---

## Installation

```bash
# No installation needed — run compiler directly
python pyplone.py myprogram.pylo --run

# For .exe compilation, install PyInstaller first:
pip install pyinstaller
python pyplone.py myprogram.pylo
```

---

## Roadmap

- v1.1: Pattern matching (`match`/`case`), deref-assign (`*p = value`)
- v1.2: Smart pointers (`unique_ptr[T]`, `shared_ptr[T]`)
- v1.3: Inline C++ interop blocks
- v1.4: Native code backend (LLVM/C transpilation)

---

*PyPLone — because sometimes you want Python's elegance AND C++'s control.*





new pyplone version:
PyPlone is a Python-based programming language that transpiles .pylo files into Python and can optionally compile them into standalone executables using PyInstaller.

It is designed as an experimental language project focused on learning compiler architecture, language design, and toolchain development.

Features

Python-like syntax

Custom lexer, parser, and AST system

Code generation to Python

Compile to standalone .exe using PyInstaller

Direct run mode (--run)

Multi-file project support

Compiler-style error messages (line + caret pointer)

VS Code syntax highlighting extension

File Extension
.pylo
Requirements

Python 3.10 or higher

PyInstaller (for building executables)

Install PyInstaller:

pip install pyinstaller
Usage
Run a file directly
pyplone main.pylo --run

This transpiles and runs without creating an executable.

Compile to executable
pyplone main.pylo

This builds:

main.exe
Emit transpiled Python only
pyplone main.pylo --py
Specify output file
pyplone main.pylo -o program.exe
Debug token stream
pyplone --tokens main.pylo
Debug AST
pyplone --ast main.pylo
Multi-File Projects

PyPlone supports importing other .pylo files inside the same project directory.

Example:

Project structure:

project/
 ├─ main.pylo
 └─ util.pylo

main.pylo

import util
print(util.add(2, 3))

util.pylo

def add(a, b):
    return a + b

Run:

pyplone main.pylo --run
Example

hello.pylo

print("Hello from PyPlone!")

Run:

pyplone hello.pylo --run

Build executable:

pyplone hello.pylo
How It Works

Compilation pipeline:

Source (.pylo)

Lexer

Parser

AST generation

Code generation (Python)

Optional PyInstaller build

Project Structure
Compiler/
 ├─ lexer.py
 ├─ parser.py
 ├─ ast_nodes.py
 ├─ codegen.py
 └─ pyplone.py
Error Diagnostics

PyPlone prints compiler-style errors including:

File name

Line number

Column

Source code snippet

Caret pointer

Example:

main.pylo:12:9: parse error: Expected RPAREN
  print(x
          ^
VS Code Extension

PyPlone includes a VS Code extension with:

Syntax highlighting

Snippets

Custom theme

To package:

cd vscode-extension
vsce package

Install the generated .vsix file in VS Code.

License

MIT License

About

PyPlone is an experimental language project built to explore compiler construction, programming language design, and custom toolchain development using Python.
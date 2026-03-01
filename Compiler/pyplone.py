#!/usr/bin/env python3

import sys
import os
import argparse
import subprocess
import tempfile
import shutil
import re

sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from codegen import Codegen, CodegenError


VERSION = "1.0.0"
FILE_EXT = ".pylo"


# ──────────────────────────────────────────────────────────────
# Python runner (works frozen + normal)
# ──────────────────────────────────────────────────────────────


def get_python_runner():
    if getattr(sys, "frozen", False):
        return shutil.which("py") or shutil.which("python") or sys.executable
    return sys.executable


# ──────────────────────────────────────────────────────────────
# Diagnostics (real compiler-style errors)
# ──────────────────────────────────────────────────────────────


def _read_line(path, line_no):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1]
    except:
        pass
    return ""


def print_diagnostic(path, line, col, kind, msg):
    if col < 1:
        col = 1

    loc = f"{path}:{line}:{col}" if line > 0 else path
    print(f"{loc}: {kind}: {msg}")

    code_line = _read_line(path, line)
    if code_line:
        print("  " + code_line)
        expanded = code_line.expandtabs(4)
        caret_pos = min(len(expanded), col - 1)
        print("  " + (" " * caret_pos) + "^")


# ──────────────────────────────────────────────────────────────
# Compilation pipeline
# ──────────────────────────────────────────────────────────────


def compile_source(source: str) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    gen = Codegen()
    return gen.generate(ast)


def compile_to_py(source_file: str, out_file: str = None) -> str:
    with open(source_file, "r", encoding="utf-8") as f:
        src = f.read()

    py_src = compile_source(src)

    if out_file is None:
        out_file = source_file.replace(FILE_EXT, ".py")

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(py_src)

    return out_file


# ──────────────────────────────────────────────────────────────
# Multi-file project support
# ──────────────────────────────────────────────────────────────

_import_re = re.compile(r"^\s*(import|get)\s+(.+)$")
_from_re = re.compile(r"^\s*from\s+([\w\.]+)\s+(import|get)\s+(.+)$")


def parse_imports(src):
    mods = set()
    for line in src.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue

        m = _import_re.match(line)
        if m:
            parts = m.group(2).split(",")
            for p in parts:
                p = p.strip().split(" as ")[0]
                if p:
                    mods.add(p)
            continue

        m = _from_re.match(line)
        if m:
            mods.add(m.group(1))

    return mods


def resolve_module(module, root):
    rel = module.replace(".", os.sep)
    cand1 = os.path.join(root, rel + FILE_EXT)
    cand2 = os.path.join(root, rel, "__init__" + FILE_EXT)

    if os.path.exists(cand1):
        return cand1
    if os.path.exists(cand2):
        return cand2
    return None


def compile_project(entry_file, build_root, verbose=False):
    project_root = os.path.dirname(os.path.abspath(entry_file))
    visited = set()

    def _compile(path):
        path = os.path.abspath(path)
        if path in visited:
            return
        visited.add(path)

        with open(path, "r", encoding="utf-8") as f:
            src = f.read()

        rel = os.path.relpath(path, project_root)
        out_py = os.path.join(build_root, os.path.splitext(rel)[0] + ".py")

        compile_to_py(path, out_py)

        if verbose:
            print(f"[PyPLone] + {rel}")

        for mod in parse_imports(src):
            dep = resolve_module(mod, project_root)
            if dep:
                _compile(dep)

    _compile(entry_file)

    rel_entry = os.path.relpath(entry_file, project_root)
    return os.path.join(build_root, os.path.splitext(rel_entry)[0] + ".py")


# ──────────────────────────────────────────────────────────────
# Run mode (multi-file aware)
# ──────────────────────────────────────────────────────────────


def run_pylo(source_file, args=None, verbose=False):
    python_runner = get_python_runner()

    with tempfile.TemporaryDirectory() as tmpdir:
        build_root = os.path.join(tmpdir, "build")
        os.makedirs(build_root, exist_ok=True)

        entry_py = compile_project(source_file, build_root, verbose)

        env = os.environ.copy()
        env["PYTHONPATH"] = build_root

        cmd = [python_runner, entry_py] + (args or [])

        if verbose:
            print("[PyPLone] Running:", " ".join(cmd))

        result = subprocess.run(cmd, env=env)
        return result.returncode


# ──────────────────────────────────────────────────────────────
# EXE build (multi-file aware)
# ──────────────────────────────────────────────────────────────


def compile_to_exe(source_file, out_file=None, verbose=False):
    base = os.path.splitext(os.path.basename(source_file))[0]
    out_dir = os.path.dirname(os.path.abspath(source_file))

    if out_file is None:
        out_file = os.path.join(out_dir, base + ".exe")

    print(f"[PyPLone] Building project → EXE")

    with tempfile.TemporaryDirectory() as tmpdir:
        build_root = os.path.join(tmpdir, "build")
        os.makedirs(build_root, exist_ok=True)

        entry_py = compile_project(source_file, build_root, verbose)

        dist_dir = os.path.join(tmpdir, "dist")
        build_dir = os.path.join(tmpdir, "work")

        cmd = [
            "py",
            "-m",
            "PyInstaller",
            "--onefile",
            "--paths",
            build_root,
            "--distpath",
            dist_dir,
            "--workpath",
            build_dir,
            "--name",
            base,
            entry_py,
        ]

        print("[PyPLone] Running:", " ".join(cmd))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("[PyPLone] PyInstaller failed!")
            print(result.stdout)
            print(result.stderr)
            sys.exit(result.returncode)

        built = os.path.join(dist_dir, base + ".exe")
        shutil.move(built, out_file)

        print(f"[PyPLone] ✓ Built: {out_file}")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(prog="pyplone")
    parser.add_argument("file", nargs="?", help=".pylo file")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--py", action="store_true")
    parser.add_argument("-o", "--output")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        return

    source_file = args.file
    if not os.path.exists(source_file):
        print("File not found.")
        return

    try:
        if args.run:
            sys.exit(run_pylo(source_file, verbose=args.verbose))
        elif args.py:
            compile_to_py(source_file)
        else:
            compile_to_exe(source_file, args.output, args.verbose)

    except LexerError as e:
        print_diagnostic(source_file, e.line, e.col, "lex error", str(e))
    except ParseError as e:
        print_diagnostic(source_file, e.line, e.col, "parse error", str(e))
    except CodegenError as e:
        print_diagnostic(source_file, 0, 0, "codegen error", str(e))
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    main()

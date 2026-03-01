#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              PyPLone Compiler  v2.0  —  PyPlone-compiler.py         ║
║  Python-like syntax · C++ pointer support · Python library access   ║
║                                                                      ║
║  Usage:                                                              ║
║    python PyPlone-compiler.py <file.pylo>          → compile to exe ║
║    python PyPlone-compiler.py <file.pylo> --run    → run directly   ║
║    python PyPlone-compiler.py <file.pylo> --py     → emit Python    ║
║    python PyPlone-compiler.py --open               → open file GUI  ║
║    python PyPlone-compiler.py --install             → register .pylo║
╚══════════════════════════════════════════════════════════════════════╝

When compiled with PyInstaller:
    PyPlone-compiler.exe hello.pylo          → compile to exe
    PyPlone-compiler.exe hello.pylo --run    → run .pylo file
    PyPlone-compiler.exe --open              → GUI file picker
    PyPlone-compiler.exe --install           → register as .pylo opener

Register as default opener for .pylo files:
    Windows: PyPlone-compiler.exe --install
    Linux:   python PyPlone-compiler.py --install
    macOS:   python PyPlone-compiler.py --install
"""

import sys
import os
import argparse
import subprocess
import tempfile
import shutil
import platform

# ── Determine if running as a PyInstaller bundle ──────────────────────────────
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    # Running as compiled .exe — compiler files are bundled
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add compiler directory to path
sys.path.insert(0, BASE_DIR)

try:
    from lexer import Lexer, LexerError
    from parser import Parser, ParseError
    from codegen import Codegen, CodegenError
except ImportError as e:
    print(f'[PyPLone] Fatal: Cannot find compiler modules: {e}')
    print(f'[PyPLone] Make sure lexer.py, parser.py, ast_nodes.py, codegen.py are alongside this file.')
    sys.exit(1)


VERSION = '2.0.0'
FILE_EXT = '.pylo'
COMPILER_NAME = 'PyPlone-compiler'

BANNER = f"""
╔══════════════════════════════════════════════════════════════════════╗
║           PyPLone Compiler v{VERSION}                              ║
║   Python syntax · C++ pointers · Full Python library access          ║
╚══════════════════════════════════════════════════════════════════════╝

  Syntax:  get <lib>           (import a Python library)
           from <lib> get *    (from-import)
           ptr[T], &x, *p      (C++ pointer ops)
           new T(), delete p   (heap management)

  Compile: python PyPlone-compiler.py hello.pylo
  Run:     python PyPlone-compiler.py hello.pylo --run
  Open:    python PyPlone-compiler.py --open
"""


# ─────────────────────────────────────────────────────────────────────────────
# Core compilation pipeline
# ─────────────────────────────────────────────────────────────────────────────

def compile_source(source: str, filename: str = '<stdin>') -> str:
    """Full pipeline: .pylo source → Python source string."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = Codegen()
    return gen.generate(ast)


def compile_to_py(source_file: str, out_file: str = None) -> str:
    """Transpile .pylo → .py. Returns path to .py file."""
    source_file = _resolve_file(source_file)
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    python_src = compile_source(source, source_file)
    if out_file is None:
        out_file = source_file.replace(FILE_EXT, '.py')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(python_src)
    return out_file


def compile_to_exe(source_file: str, out_file: str = None, verbose: bool = False,
                   windowed: bool = False) -> str:
    """Compile .pylo → .py → .exe using PyInstaller."""
    source_file = _resolve_file(source_file)
    base_name = os.path.splitext(os.path.basename(source_file))[0]
    out_dir = os.path.dirname(os.path.abspath(source_file))

    if out_file is None:
        if sys.platform == 'win32':
            out_file = os.path.join(out_dir, base_name + '.exe')
        else:
            out_file = os.path.join(out_dir, base_name)

    print(f'[PyPLone] Transpiling {os.path.basename(source_file)} → Python...')

    with tempfile.TemporaryDirectory() as tmpdir:
        py_file = os.path.join(tmpdir, base_name + '.py')
        compile_to_py(source_file, py_file)

        if verbose:
            with open(py_file) as f:
                print('\n── Transpiled Python ──────────────────────────────')
                print(f.read())
                print('───────────────────────────────────────────────────\n')

        # Check PyInstaller availability
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--version'],
            capture_output=True
        )

        if result.returncode != 0:
            # PyInstaller not available — fall back to .py with launcher
            print('[PyPLone] WARNING: PyInstaller not found.')
            print('[PyPLone] Install with: pip install pyinstaller')
            print('[PyPLone] Falling back to Python script output.')
            py_out = out_file.rstrip('.exe') + '.py' if out_file.endswith('.exe') else out_file + '.py'
            shutil.copy(py_file, py_out)
            _write_launcher(py_out)
            print(f'[PyPLone] Script saved: {py_out}')
            print(f'[PyPLone] Run with: python {py_out}')
            return py_out

        print(f'[PyPLone] Compiling to executable...')
        dist_dir = os.path.join(tmpdir, 'dist')
        build_dir = os.path.join(tmpdir, 'build')

        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--distpath', dist_dir,
            '--workpath', build_dir,
            '--specpath', tmpdir,
            '--name', base_name,
        ]
        if windowed:
            cmd.append('--windowed')
        if not verbose:
            cmd.append('--log-level=WARN')
        cmd.append(py_file)

        result = subprocess.run(cmd, capture_output=not verbose)
        if result.returncode != 0:
            print('[PyPLone] PyInstaller failed!')
            if not verbose:
                print(result.stderr.decode(errors='replace'))
            sys.exit(1)

        if sys.platform == 'win32':
            built = os.path.join(dist_dir, base_name + '.exe')
        else:
            built = os.path.join(dist_dir, base_name)

        shutil.move(built, out_file)
        print(f'[PyPLone] ✓ Compiled: {out_file}')
        return out_file


def run_pylo(source_file: str, extra_args: list = None, verbose: bool = False) -> int:
    """Transpile and run a .pylo file directly."""
    source_file = _resolve_file(source_file)
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    python_src = compile_source(source, source_file)

    if verbose:
        print('\n── Transpiled Python ──────────────────────────────')
        print(python_src)
        print('───────────────────────────────────────────────────\n')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                    delete=False, encoding='utf-8') as tmp:
        tmp.write(python_src)
        tmp_path = tmp.name

    try:
        cmd = [sys.executable, tmp_path] + (extra_args or [])
        result = subprocess.run(cmd)
        return result.returncode
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# OS Registration — .pylo file association
# ─────────────────────────────────────────────────────────────────────────────

def install_file_association():
    """Register this compiler as the default opener for .pylo files."""
    system = platform.system()
    exe = sys.executable if not IS_FROZEN else os.path.abspath(sys.argv[0])
    compiler = os.path.abspath(__file__) if not IS_FROZEN else exe

    if system == 'Windows':
        _install_windows(exe, compiler)
    elif system == 'Linux':
        _install_linux(exe, compiler)
    elif system == 'Darwin':
        _install_macos(exe, compiler)
    else:
        print(f'[PyPLone] Auto-install not supported on {system}.')
        print(f'[PyPLone] Manually associate .pylo files with: {compiler}')


def _install_windows(exe, compiler):
    """Register .pylo via Windows registry."""
    try:
        import winreg
        # Associate .pylo extension
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, '.pylo') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, 'PyPLoneFile')

        # Register file type
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, 'PyPLoneFile') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, 'PyPLone Source File')

        # Register open command
        open_cmd = f'"{compiler}" "%1" --run' if IS_FROZEN else f'"{exe}" "{compiler}" "%1" --run'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT,
                              r'PyPLoneFile\shell\open\command') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, open_cmd)

        # Register compile command
        compile_cmd = f'"{compiler}" "%1"' if IS_FROZEN else f'"{exe}" "{compiler}" "%1"'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT,
                              r'PyPLoneFile\shell\Compile\command') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, compile_cmd)

        # Notify shell of change
        try:
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        except Exception:
            pass

        print('[PyPLone] ✓ Registered .pylo file association on Windows.')
        print('[PyPLone]   Double-click any .pylo file to run it.')
        print('[PyPLone]   Right-click → "Compile" to build an executable.')
    except PermissionError:
        print('[PyPLone] ERROR: Need administrator rights to register file type.')
        print('[PyPLone] Run this command as Administrator.')
    except Exception as e:
        print(f'[PyPLone] Registration failed: {e}')


def _install_linux(exe, compiler):
    """Register .pylo on Linux via .desktop file and xdg-mime."""
    home = os.path.expanduser('~')
    apps_dir = os.path.join(home, '.local', 'share', 'applications')
    mime_dir = os.path.join(home, '.local', 'share', 'mime', 'packages')
    os.makedirs(apps_dir, exist_ok=True)
    os.makedirs(mime_dir, exist_ok=True)

    # MIME type file
    mime_xml = os.path.join(mime_dir, 'pyplone.xml')
    with open(mime_xml, 'w') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/x-pyplone">
    <comment>PyPLone Source File</comment>
    <glob pattern="*.pylo"/>
  </mime-type>
</mime-info>
''')

    # Desktop entry
    open_cmd = compiler if IS_FROZEN else f'{exe} {compiler}'
    desktop = os.path.join(apps_dir, 'pyplone.desktop')
    with open(desktop, 'w') as f:
        f.write(f'''[Desktop Entry]
Name=PyPLone Compiler
Comment=Run or compile PyPLone .pylo files
Exec={open_cmd} %f --run
Icon=utilities-terminal
Terminal=true
Type=Application
MimeType=text/x-pyplone;
Categories=Development;
''')

    # Register MIME type
    subprocess.run(['update-mime-database',
                    os.path.join(home, '.local', 'share', 'mime')],
                   capture_output=True)
    subprocess.run(['update-desktop-database', apps_dir], capture_output=True)
    subprocess.run(['xdg-mime', 'default', 'pyplone.desktop', 'text/x-pyplone'],
                   capture_output=True)

    print('[PyPLone] ✓ Registered .pylo file association on Linux.')
    print(f'[PyPLone]   MIME: {mime_xml}')
    print(f'[PyPLone]   Desktop: {desktop}')


def _install_macos(exe, compiler):
    """Register .pylo on macOS via Info.plist approach (basic)."""
    # Create a shell script launcher
    launcher = os.path.expanduser('~/bin/pyplone-open')
    os.makedirs(os.path.dirname(launcher), exist_ok=True)
    open_cmd = compiler if IS_FROZEN else f'{exe} {compiler}'
    with open(launcher, 'w') as f:
        f.write(f'#!/bin/bash\n{open_cmd} "$1" --run\n')
    os.chmod(launcher, 0o755)
    print('[PyPLone] ✓ Created launcher at ~/bin/pyplone-open')
    print('[PyPLone]   Run a .pylo file: pyplone-open hello.pylo')
    print('[PyPLone]   For full .pylo association, create an Automator app.')


# ─────────────────────────────────────────────────────────────────────────────
# GUI file opener (when double-clicked or --open flag)
# ─────────────────────────────────────────────────────────────────────────────

def open_file_gui():
    """Open a file picker GUI to select and run/compile a .pylo file."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError:
        print('[PyPLone] tkinter not available. Please specify a file directly.')
        print('Usage: python PyPlone-compiler.py <file.pylo>')
        return

    root = tk.Tk()
    root.title('PyPLone Compiler v2.0')
    root.geometry('500x380')
    root.configure(bg='#1e1e2e')
    root.resizable(False, False)

    # Title
    tk.Label(root, text='PyPLone Compiler', font=('Consolas', 18, 'bold'),
             fg='#cba6f7', bg='#1e1e2e').pack(pady=(20, 5))
    tk.Label(root, text='Python syntax · C++ pointers · .pylo files',
             font=('Consolas', 9), fg='#6c7086', bg='#1e1e2e').pack(pady=(0, 20))

    # File selector
    selected_file = tk.StringVar(value='No file selected')

    file_frame = tk.Frame(root, bg='#313244', relief='flat')
    file_frame.pack(padx=20, fill='x', pady=5)

    tk.Label(file_frame, textvariable=selected_file, font=('Consolas', 9),
             fg='#cdd6f4', bg='#313244', wraplength=380, anchor='w').pack(
        side='left', padx=10, pady=8, fill='x', expand=True)

    def browse():
        path = filedialog.askopenfilename(
            title='Select a .pylo file',
            filetypes=[('PyPLone files', '*.pylo'), ('All files', '*.*')]
        )
        if path:
            selected_file.set(path)

    tk.Button(file_frame, text='Browse', font=('Consolas', 9),
              bg='#45475a', fg='#cdd6f4', relief='flat', cursor='hand2',
              command=browse, padx=10).pack(side='right', padx=5, pady=5)

    # Output log
    log_frame = tk.Frame(root, bg='#1e1e2e')
    log_frame.pack(padx=20, pady=10, fill='both', expand=True)

    log = tk.Text(log_frame, height=8, font=('Consolas', 9),
                  bg='#11111b', fg='#cdd6f4', relief='flat',
                  insertbackground='#cba6f7', state='disabled')
    log.pack(fill='both', expand=True)

    def log_msg(msg, color='#cdd6f4'):
        log.configure(state='normal')
        log.insert('end', msg + '\n')
        log.configure(state='disabled')
        log.see('end')

    def do_run():
        f = selected_file.get()
        if not os.path.exists(f):
            messagebox.showerror('Error', 'Please select a valid .pylo file first.')
            return
        log_msg(f'▶ Running {os.path.basename(f)}...', '#a6e3a1')
        try:
            src = open(f, 'r', encoding='utf-8').read()
            py_src = compile_source(src, f)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                            delete=False, encoding='utf-8') as tmp:
                tmp.write(py_src)
                tmp_path = tmp.name
            result = subprocess.run([sys.executable, tmp_path],
                                    capture_output=True, text=True)
            os.unlink(tmp_path)
            if result.stdout:
                log_msg(result.stdout.rstrip(), '#a6e3a1')
            if result.stderr:
                log_msg(result.stderr.rstrip(), '#f38ba8')
            log_msg(f'Done (exit {result.returncode})')
        except Exception as e:
            log_msg(f'Error: {e}', '#f38ba8')

    def do_compile():
        f = selected_file.get()
        if not os.path.exists(f):
            messagebox.showerror('Error', 'Please select a valid .pylo file first.')
            return
        log_msg(f'⚙ Compiling {os.path.basename(f)}...', '#89b4fa')
        try:
            compile_to_exe(f, verbose=False)
            log_msg('✓ Compiled successfully!', '#a6e3a1')
        except Exception as e:
            log_msg(f'Error: {e}', '#f38ba8')

    def do_py():
        f = selected_file.get()
        if not os.path.exists(f):
            messagebox.showerror('Error', 'Please select a valid .pylo file first.')
            return
        out = compile_to_py(f)
        log_msg(f'✓ Python source: {out}', '#a6e3a1')

    # Buttons
    btn_frame = tk.Frame(root, bg='#1e1e2e')
    btn_frame.pack(pady=10)

    for text, cmd, color in [
        ('▶  Run', do_run, '#a6e3a1'),
        ('⚙  Compile .exe', do_compile, '#89b4fa'),
        ('📄  Emit Python', do_py, '#fab387'),
    ]:
        tk.Button(btn_frame, text=text, font=('Consolas', 10, 'bold'),
                  bg='#313244', fg=color, relief='flat', cursor='hand2',
                  command=cmd, padx=16, pady=6).pack(side='left', padx=8)

    log_msg('PyPLone Compiler v2.0 ready.')
    log_msg('Select a .pylo file and choose an action.')

    root.mainloop()


# ─────────────────────────────────────────────────────────────────────────────
# Debug / Introspection
# ─────────────────────────────────────────────────────────────────────────────

def show_tokens(source_file: str):
    source_file = _resolve_file(source_file)
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f'Tokens for {source_file}:')
    print('─' * 60)
    for tok in tokens:
        print(f'  {tok.type.name:20s} {tok.value!r:30s}  @{tok.line}:{tok.col}')
    print(f'\nTotal: {len(tokens)} tokens')


def show_ast(source_file: str):
    source_file = _resolve_file(source_file)
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    tree = parser.parse()

    def _dump(node, indent=0):
        prefix = '  ' * indent
        cls = type(node).__name__
        fields = {k: v for k, v in vars(node).items()
                  if k not in ('line', 'col') and v is not None}
        if not fields:
            print(f'{prefix}{cls}()')
            return
        print(f'{prefix}{cls}(')
        for k, v in fields.items():
            if isinstance(v, list):
                if v:
                    print(f'{prefix}  {k}=[')
                    for item in v:
                        if hasattr(item, '__dict__'):
                            _dump(item, indent + 2)
                        else:
                            print(f'{prefix}    {item!r}')
                    print(f'{prefix}  ]')
            elif hasattr(v, '__dict__'):
                print(f'{prefix}  {k}=')
                _dump(v, indent + 2)
            else:
                print(f'{prefix}  {k}={v!r}')
        print(f'{prefix})')
    _dump(tree)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_file(path: str) -> str:
    if os.path.exists(path):
        return path
    with_ext = path + FILE_EXT
    if os.path.exists(with_ext):
        return with_ext
    raise FileNotFoundError(f'File not found: {path}')


def _write_launcher(py_file: str):
    """Write a .bat/.sh launcher next to the .py file."""
    base = os.path.splitext(py_file)[0]
    if sys.platform == 'win32':
        bat = base + '.bat'
        with open(bat, 'w') as f:
            f.write(f'@echo off\npython "{py_file}" %*\n')
        print(f'[PyPLone] Launcher: {bat}')
    else:
        sh = base + '.sh'
        with open(sh, 'w') as f:
            f.write(f'#!/bin/bash\npython3 "{py_file}" "$@"\n')
        os.chmod(sh, 0o755)
        print(f'[PyPLone] Launcher: {sh}')


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # If a .pylo file was double-clicked and passed as the only arg,
    # open GUI with that file pre-selected (or just run it)
    if len(sys.argv) == 2 and sys.argv[1].endswith(FILE_EXT) and os.path.isfile(sys.argv[1]):
        # Opened by double-click or file association
        if IS_FROZEN:
            # In a compiled exe: show GUI with file loaded
            try:
                import tkinter
                _run_with_gui(sys.argv[1])
                return
            except ImportError:
                pass
        # Fallback: just run it
        sys.exit(run_pylo(sys.argv[1]))

    parser = argparse.ArgumentParser(
        prog=COMPILER_NAME,
        description='PyPLone Compiler — Python syntax with C++ pointer support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Keywords:
  get <lib>              import a Python library  (alias for 'import')
  from <lib> get <name>  from-import              (alias for 'from ... import')
  ptr[T], new, delete    C++ pointer semantics
  &x, *p, x->field      address-of, deref, ptr-member

Examples:
  PyPlone-compiler.py hello.pylo              Compile to executable
  PyPlone-compiler.py hello.pylo --run        Run directly
  PyPlone-compiler.py hello.pylo --py         Emit Python source
  PyPlone-compiler.py --open                  GUI file picker
  PyPlone-compiler.py --install               Register .pylo opener
  PyPlone-compiler.py --tokens hello.pylo     Debug: token stream
  PyPlone-compiler.py --ast hello.pylo        Debug: AST
        """
    )

    parser.add_argument('file', nargs='?', help='.pylo source file')
    parser.add_argument('-o', '--output', help='Output path')
    parser.add_argument('--py', action='store_true', help='Emit Python source only')
    parser.add_argument('--run', action='store_true', help='Run directly (no exe)')
    parser.add_argument('--open', action='store_true', help='Open GUI file picker')
    parser.add_argument('--install', action='store_true', help='Register as .pylo file opener')
    parser.add_argument('--windowed', action='store_true', help='Compile GUI app (no console)')
    parser.add_argument('--tokens', action='store_true', help='Show token stream (debug)')
    parser.add_argument('--ast', action='store_true', help='Show AST (debug)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version=f'PyPLone {VERSION}')

    args, rest = parser.parse_known_args()

    if args.open or (not args.file and not args.install):
        if not args.file and not args.install:
            open_file_gui()
            return

    if args.install:
        install_file_association()
        return

    if not args.file:
        print(BANNER)
        parser.print_help()
        return

    try:
        if args.tokens:
            show_tokens(args.file)
        elif args.ast:
            show_ast(args.file)
        elif args.run:
            sys.exit(run_pylo(args.file, rest, verbose=args.verbose))
        elif args.py:
            out = args.output or args.file.replace(FILE_EXT, '.py')
            compile_to_py(args.file, out)
            print(f'[PyPLone] Python source: {out}')
        else:
            compile_to_exe(args.file, args.output, verbose=args.verbose,
                           windowed=args.windowed)

    except FileNotFoundError as e:
        print(f'[PyPLone] {e}')
        sys.exit(1)
    except LexerError as e:
        print(f'[PyPLone] Lex error: {e}')
        sys.exit(1)
    except ParseError as e:
        print(f'[PyPLone] Parse error: {e}')
        sys.exit(1)
    except CodegenError as e:
        print(f'[PyPLone] Codegen error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[PyPLone] Error: {e}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _run_with_gui(pylo_file: str):
    """Open GUI with a specific file pre-selected."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title(f'PyPLone — {os.path.basename(pylo_file)}')
    root.geometry('420x200')
    root.configure(bg='#1e1e2e')

    tk.Label(root, text='PyPLone Compiler', font=('Consolas', 14, 'bold'),
             fg='#cba6f7', bg='#1e1e2e').pack(pady=15)
    tk.Label(root, text=os.path.basename(pylo_file),
             font=('Consolas', 10), fg='#89b4fa', bg='#1e1e2e').pack()

    btn_frame = tk.Frame(root, bg='#1e1e2e')
    btn_frame.pack(pady=20)

    def do_run():
        root.destroy()
        sys.exit(run_pylo(pylo_file))

    def do_compile():
        root.destroy()
        compile_to_exe(pylo_file)

    tk.Button(btn_frame, text='▶  Run', font=('Consolas', 11, 'bold'),
              bg='#313244', fg='#a6e3a1', relief='flat', cursor='hand2',
              command=do_run, padx=20, pady=8).pack(side='left', padx=10)

    tk.Button(btn_frame, text='⚙  Compile .exe', font=('Consolas', 11, 'bold'),
              bg='#313244', fg='#89b4fa', relief='flat', cursor='hand2',
              command=do_compile, padx=20, pady=8).pack(side='left', padx=10)

    root.mainloop()


if __name__ == '__main__':
    main()

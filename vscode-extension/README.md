# PyPLone VS Code Extension

Syntax highlighting, snippets, run/compile commands, and a custom dark theme
for **PyPLone** (`.pylo`) — Python-like syntax with C++ pointer support.

## Installation

### Option A — From .vsix File (Recommended)

1. Download `pyplone-2.0.0.vsix`
2. Open VS Code
3. Press `Ctrl+Shift+P` → type **"Install from VSIX"**
4. Select the downloaded `.vsix` file
5. Reload VS Code

### Option B — Manual Install

Copy the `vscode-extension/` folder to your VS Code extensions directory:

| OS      | Path |
|---------|------|
| Windows | `%USERPROFILE%\.vscode\extensions\pyplone` |
| macOS   | `~/.vscode/extensions/pyplone` |
| Linux   | `~/.vscode/extensions/pyplone` |

Then reload VS Code.

### Option C — Build and Install with vsce

```bash
npm install -g @vscode/vsce
cd vscode-extension
vsce package
code --install-extension pyplone-2.0.0.vsix
```

## Features

### Syntax Highlighting

Full tokenisation of all PyPLone constructs:

| Element | Color |
|---------|-------|
| `get`, `from ... get` | Cyan (import keywords) |
| `ptr`, `new`, `delete`, `nullptr` | Red/Pink (pointer keywords) |
| `->`, `&` operators | Red/Pink |
| `def`, `class` | Purple bold |
| `if`, `for`, `while`, `return` | Purple |
| Type names (`int`, `float`, `str`) | Blue |
| Strings & f-strings | Green |
| Numbers | Peach/Orange |
| Comments | Grey italic |
| Decorators | Pink italic |
| Built-in functions | Cyan |

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| **PyPLone: Run File** | `F5` | Run `.pylo` directly |
| **PyPLone: Compile to Executable** | — | Build `.exe` with PyInstaller |
| **PyPLone: Emit Transpiled Python** | — | Show generated Python side-by-side |

### Snippets

| Prefix | Inserts |
|--------|---------|
| `def` | Function definition |
| `class` | Class definition |
| `ptr` | Pointer variable |
| `new` | Heap allocation |
| `delete` | Free pointer |
| `get` | Import library |
| `fromget` | From-import |
| `tkwindow` | Basic tkinter GUI window |
| `lc` | List comprehension |
| `dc` | Dict comprehension |
| `try` | Try-except block |
| `var` | Typed variable |
| `node` | Linked list node |

### Theme

Select **PyPLone Dark** from `File → Preferences → Color Theme`.

Catppuccin-inspired dark theme with distinct colors for pointer operations.

## Configuration

In VS Code settings (`settings.json`):

```json
{
  "pyplone.compilerPath": "python /path/to/PyPlone-compiler.py",
  "pyplone.showTranspiledOutput": false
}
```

## Example `.pylo` File

```pylo
# hello.pylo
get tkinter as tk

def greet(name: str) -> str:
    return f"Hello, {name}!"

root = tk.Tk()
root.title("PyPLone GUI")
tk.Label(root, text=greet("World"), font=("Arial", 18)).pack(pady=20)
root.mainloop()
```

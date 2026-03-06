# PyPlone VS Code Extension

A fresh VS Code extension for **PyPlone** with a cleaner language identity.

## New syntax vibe

PyPlone now highlights words like:

- `seed` for functions
- `grove` for classes
- `branch` / `otherwise if` / `otherwise`
- `let`, `give`, `stop`, `skip`, `rest`
- `yes`, `no`, `nothing`
- `bloom gui`, `leaf`, `text`, `field`, `popup`, `on tap`
- `get`, `take ... from ...`

## Commands

- **PyPlone: Run File**
- **PyPlone: Compile to Executable**
- **PyPlone: Emit Python**

By default the extension looks for:

- `Compiler/pyp.bat`
- `Compiler/pap.bat`

inside your workspace.

## Example

```pylo
bloom gui "Leaf App":
    size 320, 200
    tint "#dff5e3"

    text "Hello from PyLo!"
    leaf "Press":
        on tap:
            popup "PyLo", "No console GUI working!"
```

## Install

Copy this folder into your VS Code extensions directory or package it with `vsce package`.

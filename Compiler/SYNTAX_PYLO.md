# PyPlone Nature Syntax

This version gives PyPlone its own vibe instead of looking like a Python clone.
It still stays easy.

## Core words

- `seed` = make a function
- `grove` = make a class
- `branch` = if
- `otherwise if` = elif
- `otherwise` = else
- `let` = set a variable
- `give` = return
- `stop` = break
- `skip` = continue
- `rest` = pass
- `yes` / `no` = true / false
- `nothing` = none
- `get` = import
- `take x get y` = from x import y
- `echo()` = print()

## Example

```py
get math

aura = "forest"

seed add(a, b):
    let total = a + b
    give total

seed mood(score):
    branch score >= 10:
        echo("wild")
    otherwise if score >= 5:
        echo("calm")
    otherwise:
        echo("sleepy")

grove Player:
    seed __init__(self, name):
        let self.name = name
        let self.hp = 100

    seed heal(self, amount):
        let self.hp = self.hp + amount
        give self.hp
```

## Tiny rules

Keep Python indentation.
Still end block lines with `:`.
Anything not using a special PyPlone word passes through to Python.
That means Ursina code still works great.

## Example shooter style

```py
get ursina
from ursina import *

app = Ursina()

seed shoot():
    echo("pew")

branch held_keys["left mouse"]:
    shoot()
```

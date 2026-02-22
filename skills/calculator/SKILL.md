---
name: calculator
description: "Perform mathematical calculations using Python's eval() or custom functions."
---

# Calculator Skill

Use this skill when you need to perform mathematical calculations.

## Basic Calculations

You can use Python's built-in arithmetic:

```python
result = 2 + 2  # 4
result = 10 * 5  # 50
result = 100 / 3  # 33.333...
result = 2 ** 10  # 1024
```

## Using Bash

You can also use `bc` command:

```bash
echo "scale=2; 10/3" | bc
```

## Scripts

- [scripts/calculate.py](scripts/calculate.py) - Advanced calculations

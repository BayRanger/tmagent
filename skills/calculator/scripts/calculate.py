#!/usr/bin/env python3
"""Advanced calculator script."""

import sys


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        # Only allow safe operators
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters in expression"
        
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calculate.py <expression>")
        print("Example: python calculate.py '2+2*3'")
        sys.exit(1)
    
    expr = " ".join(sys.argv[1:])
    print(calculate(expr))

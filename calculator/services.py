"""
Safe mathematical expression evaluator.

Uses Python's ast module to parse expressions and only allows a whitelist of
math-related nodes. User input is never passed to eval() or exec().
"""

import ast
import math
import operator
import re


class CalculatorError(Exception):
    """Raised when an expression cannot be safely evaluated."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


# Characters allowed in a mathematical expression (after whitespace strip).
_ALLOWED_CHARS = re.compile(r"^[0-9+\-*/().\s]+$")

# Guard against pathological / deeply nested input.
_MAX_EXPRESSION_LENGTH = 255
_MAX_AST_DEPTH = 50

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_expression(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.

    Supports: +, -, *, /, decimals, parentheses, and unary +/-.
    Raises CalculatorError for invalid, empty, or malicious input.
    """
    if expression is None or not str(expression).strip():
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Expression is required and cannot be empty.",
        )

    expression = str(expression).strip()

    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Expression is too long.",
        )

    if not _ALLOWED_CHARS.match(expression):
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Invalid mathematical expression. Only numbers and + - * / ( ) are allowed.",
        )

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Invalid mathematical expression.",
        ) from None

    try:
        result = _eval_node(tree.body, depth=0)
    except CalculatorError:
        raise
    except ZeroDivisionError:
        raise CalculatorError(
            "DIVISION_BY_ZERO",
            "Division by zero is not allowed.",
        ) from None
    except Exception:
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Invalid mathematical expression.",
        ) from None

    if isinstance(result, complex) or not isinstance(result, (int, float)):
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Invalid mathematical expression.",
        )

    result = float(result)
    if not math.isfinite(result):
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Expression result is out of range.",
        )

    return result


def _eval_node(node, depth):
    """Recursively evaluate an AST node, allowing only safe math operations."""
    if depth > _MAX_AST_DEPTH:
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Expression is too complex.",
        )

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise CalculatorError(
            "INVALID_EXPRESSION",
            "Invalid mathematical expression.",
        )

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINARY_OPS:
            raise CalculatorError(
                "INVALID_EXPRESSION",
                "Unsupported operator.",
            )
        left = _eval_node(node.left, depth + 1)
        right = _eval_node(node.right, depth + 1)
        return _BINARY_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError(
                "INVALID_EXPRESSION",
                "Unsupported operator.",
            )
        return _UNARY_OPS[op_type](_eval_node(node.operand, depth + 1))

    # Reject names, calls, attributes, imports, subscripts, etc.
    raise CalculatorError(
        "INVALID_EXPRESSION",
        "Invalid mathematical expression.",
    )

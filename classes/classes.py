from dataclasses import dataclass
from typing import Union

@dataclass
class Var:
    name: str

@dataclass
class Not:
    x: "Expr"

@dataclass
class And:
    left: "Expr"
    right: "Expr"

@dataclass
class Or:
    left: "Expr"
    right: "Expr"

@dataclass
class Assign:
    target: Var
    expr: "Expr"

Expr = Union[Var, Not, And, Or, Assign]

def emit_expr(expr: Expr):
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, Not):
        return f"NOT {emit_expr(expr.x)}"
    if isinstance(expr, And):
        return f"{emit_expr(expr.left)} AND {emit_expr(expr.right)}"
    if isinstance(expr, Or):
        return f"{emit_expr(expr.left)} OR {emit_expr(expr.right)}"
    if isinstance(expr, Assign):
        return f"{emit_expr(expr.target)} := {emit_expr(expr.expr)}\n"

from dataclasses import dataclass
from typing import Union

@dataclass
class Var:
    name: str

@dataclass
class Not:
    expr: "Expr"

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
    if isinstance(expr, And):
        return f"{expr.left} AND {expr.right}"

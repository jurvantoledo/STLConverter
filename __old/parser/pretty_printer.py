from dataclasses import dataclass
from typing import Union, List, Optional

# --- AST Node types ---
@dataclass
class Var:  name: str
@dataclass
class Lit:  value: bool
@dataclass
class Num:  value: str # Union[int, float]
@dataclass
class Not:  x: 'Expr'
@dataclass
class And:  a: 'Expr'; b: 'Expr'
@dataclass
class Or:   a: 'Expr'; b: 'Expr'
@dataclass
class BinOp: op: str; a: 'Expr'; b: 'Expr'  # e.g. +, -, *, /
@dataclass
class CompOp: op: str; a: 'Expr'; b: 'Expr' # e.g. >= <= <>

Expr = Union[Var, Lit, Num, Not, And, Or, BinOp, CompOp]

# --- Group marker for parentheses ---
@dataclass
class GroupMarker:
    kind: str # "AND" or "OR"
    saved: Optional[Expr] # expression before entering group

def emit_expr(e: Expr) -> str:
    if isinstance(e, Var): return e.name
    if isinstance(e, Num): return e.value
    if isinstance(e, Lit): return "TRUE" if e.value else "False"
    if isinstance(e, Not): return f"NOT {emit_expr(e.x)}"
    if isinstance(e, And): return f"{emit_expr(e.a)} AND {emit_expr(e.b)}"
    if isinstance(e, Or): return f"{emit_expr(e.a)} OR {emit_expr(e.b)}"
    if isinstance(e, BinOp): return f"{emit_expr(e.a)} {e.op} {emit_expr(e.b)}"
    if isinstance(e, CompOp): return f"{emit_expr(e.a)} {e.op} {emit_expr(e.b)}"

    raise TypeError(e)
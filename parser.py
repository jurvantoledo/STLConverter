from typing import List, Optional
from classes.classes import Expr, emit_expr, Var, And, Or, Assign

class STLConverter:
    def __init__(self):
        self.expr: Optional[Expr] = None
        self.output: List[str] = []

        # Stack to push instructions if not all conditions are made
        self.stack: List[Expr] = []
    
    def close_region(self):
        self.output.append(f'END_REGION')
        return
    
    def handle_comment(self, type: str, value: str):
        if type == "COMMENT":
            self.output.append(f"{value}")
            return

    def handle_networks(self, type: str, value: str):
        if type == "TITLE":
            self.output.append(f'REGION "{value}"')
            return
    
    def convert_and(self, operand: str):
        self.stack.append(Var(operand))
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()
            self.expr = And(left=left, right=right)
            self.stack.append(self.expr)
        return self.expr
    
    def convert_or(self, operand: str):
        self.stack.append(Var(operand))
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()
            self.expr = Or(left=left, right=right)
            self.stack.append(self.expr)
        return self.expr
    
    def store_assignment(self, operand: str):
        target = Var(operand)
        condition = emit_expr(self.expr)
        scl_code = f"IF {condition} THEN\n{target.name} := true;\nELSE\n {target.name} := false;\nEND_IF;\n"
        self.output.append(scl_code)
        self.expr = None
        self.stack.clear()
        return
    
    def convert_bools(self, opcode: str, operand: str):
        if opcode == "A":
            self.convert_and(operand)
        if opcode == "O":
            self.convert_or(operand)
        if opcode == "=":
            self.store_assignment(operand=operand)
        return
    
    def store_transfers(self, dest: str):
        if self.stack:
            var = self.stack[-1]
            
            self.expr = emit_expr(Assign(target=dest, expr=var))
            self.output.append(self.expr)

    def convert_transfers(self, opcode: str, operand: str):
        if opcode == "L":
            self.stack.append(Var(operand))
        if opcode == "T":
            self.store_transfers(Var(operand))
        return self.expr

    def convert(self, opcode: str, operand: str):
        if opcode in ("A", "AN", "O", "ON", "SET", "CLR", "="):
            self.convert_bools(opcode=opcode, operand=operand)
        if opcode in ("L", "T"):
            self.convert_transfers(opcode=opcode, operand=operand)
            
    def ret_output(self):
        # print(self.output)
        self.close_region()
        return self.output

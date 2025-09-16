from typing import List, Optional
from classes.classes import Expr, emit_expr, Var, Not, And, Or, Assign

class STLConverter:
    def __init__(self):
        self.expr: Optional[Expr] = None
        self.output: List[str] = []

        # Stack to push instructions if not all conditions are made
        self.stack: List[Expr] = []
        self.opcode_stack: List[str] = []
    
    def close_region(self):
        self.expr = None
        self.stack.clear()
        self.opcode_stack.clear()
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
        self.stack.append(operand)
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()
            self.expr = And(left=left, right=right)
            self.stack.append(self.expr)
        return self.expr
    
    def convert_or(self, operand: str):
        self.stack.append(operand)
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()
            self.expr = Or(left=left, right=right)
            self.stack.append(self.expr)
        return self.expr
    
    def store_assignment(self, operand: Var):
        target = operand
        condition = emit_expr(self.expr)
        scl_code = f"IF {condition} THEN\n{target.name} := true;\nELSE\n {target.name} := false;\nEND_IF;\n"
        self.output.append(scl_code)
        self.expr = None
        self.stack.clear()
        return

    def store_set_clr(self, operand: Var):
        target = operand
        if self.opcode_stack:
            opcode = self.opcode_stack[-1] #peek
            if opcode == "SET":
                scl_code = f"{target.name} := true;\n"
            else:
                scl_code = f"{target.name} := false;\n"
            self.output.append(scl_code)
        return
    
    def convert_bools(self, opcode: str, operand: str):
        if opcode == "SET" or opcode == "CLR":
            self.opcode_stack.append(opcode)
            return
        if opcode == "A":
            self.opcode_stack.clear()
            self.convert_and(Var(operand))
        if opcode == "AN":
            self.opcode_stack.clear()
            self.convert_and(Not(Var(operand)))
        if opcode == "O":
            self.opcode_stack.clear()
            self.convert_or(Var(operand))
        if opcode == "ON":
            self.opcode_stack.clear()
            self.convert_or(Not(Var(operand)))
        if opcode == "=":
            if self.opcode_stack:
                self.store_set_clr(Var(operand))  # consume SET/CLR
            else:
                self.store_assignment(Var(operand))
        return
    
    def store_transfers(self, dest: str):
        if self.stack:
            var = self.stack[-1]
        
            self.expr = emit_expr(Assign(target=dest, expr=var))
            self.output.append(self.expr)
            self.expr = None
            self.stack.clear()
        return

    def convert_transfers(self, opcode: str, operand: str):
        if opcode == "L":
            self.stack.append(Var(operand))
        if opcode == "T":
            self.store_transfers(Var(operand))
        return self.expr

    def convert(self, opcode: str, operand: str):
        # if opcode in ("SET", "CLR"):
        #     self.convert_bools(opcode=opcode, operand=operand)

        if opcode in ("A", "AN", "O", "ON", "SET", "CLR", "="):
            self.convert_bools(opcode=opcode, operand=operand)

        if opcode in ("L", "T"):
            self.convert_transfers(opcode=opcode, operand=operand)
            
    def ret_output(self):
        # print(self.output)
        self.close_region()
        return self.output

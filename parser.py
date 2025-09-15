from typing import List
from classes.classes import emit_expr, Var, And, Or, Assign

class STLConverter:
    def __init__(self):
        self.expr = None
        self.output = []

        # Stack to push instructions if not all conditions are made
        self.stack = []
    
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
        scl_code = f"IF {condition} THEN\n{target.name} := true\nELSE\n {target.name} := false\nEND_IF;"
        self.output.append(scl_code)
        self.expr = None
        self.stack.clear()
        return
    
    def convert_bools(self, opcode, operand):
        if opcode == "A":
            self.convert_and(operand)
        if opcode == "O":
            self.convert_or(operand)
        if opcode == "=":
            self.store_assignment(operand=operand)
        return

    def convert(self, opcode: str, operand: str):
        if opcode in ("A", "AN", "O", "ON", "SET", "CLR", "="):
            self.convert_bools(opcode=opcode, operand=operand)
            
    def ret_output(self):
        # print(self.output)
        self.close_region()
        return self.output

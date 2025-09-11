from typing import List
from classes.classes import emit_expr, And, Or

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
            self.close_region()
            return


    def convert(self, opcode: str, operand: str):
        left = None
        right = None
        target = None

        if opcode == "A":
            self.stack.append(operand)

            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                self.expr = f"IF {emit_expr(And(left=left, right=right))} THEN"
                print(self.expr)
        if opcode == "=":
            target = operand
    
    
    def ret_output(self):
        return self.output

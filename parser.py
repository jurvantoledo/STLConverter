from typing import List, Optional
from stl_operators import arithmetic_operators, comparison_operators, conv_instructions, conversion_instructions
from classes.classes import Expr, emit_expr, Var, Not, And, Or, BinOp, Assign

class STLConverter:
    def __init__(self):
        self.expr: Optional[Expr] = None
        self.output: List[str] = []
        self.op = None
        # Stack to push instructions if not all conditions are made
        self.stack: List[Expr] = []
        self.opcode_stack: List[str] = []
        self.conv_instr_stack: List['Expr'] = []

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
        if opcode == "SET" or opcode == "CLR" or operand is None:
            self.opcode_stack.append(opcode)
            return
        if opcode == "A" or opcode == "A(":
            self.opcode_stack.clear()
            self.convert_and(Var(operand))
        if opcode == "AN" or opcode == "AN(":
            self.opcode_stack.clear()
            self.convert_and(Not(Var(operand)))
        if opcode == "O" or opcode == "O(":
            self.opcode_stack.clear()
            self.convert_or(Var(operand))
        if opcode == "ON" or opcode == "ON(":
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
        return

    def convert_transfers(self, opcode: str, operand: str):
        if opcode == "L":
            self.stack.append(Var(operand))
        if opcode == "T":
            self.store_transfers(Var(operand))
        return self.expr
    
    def store_arithmetic_transfers(self, op: str, dest: str):
        if len(self.stack) >= 2:
            left = self.stack.pop()
            right = self.stack.pop()
        
            condition = BinOp(left=left, op=op, right=right)
            self.expr = emit_expr(Assign(target=dest, expr=condition))
            self.output.append(self.expr)
            self.expr = None
            self.op = None
            self.stack.clear()
        return
        
    def convert_arithmetic_operators(self, opcode, op, operand):
        if op:
            if opcode == "L":
                self.stack.append(Var(operand))
            if opcode == "T":
                self.store_arithmetic_transfers(op, Var(operand))
            return

    def convert_conv_instructions(self, opcode, operand):
        if opcode == "L":
            self.stack.append(Var(operand))
        
        stack_val = self.stack[-1]

        if opcode == "T":
            if len(self.conv_instr_stack) >= 2:
                test = "(".join(self.conv_instr_stack)
                test2 = test + f"({stack_val.name}" + ")" * len(self.conv_instr_stack)
                print(f"TEST: {test2}")
                return
            else:
                for instr in self.conv_instr_stack:
                    val = Var(f"{instr}({stack_val.name})")
                
                self.conv_instr_stack.pop()
                self.expr = emit_expr(Assign(target=Var(operand), expr=val))
                self.output.append(self.expr)

            print(f"Final assignment: {self.expr}")
            self.expr = None
        return

    # def convert_conv_instructions(self, opcode, operand):
    #     # Expect to be called only for opcode == "T"
    #     if opcode != "T":
    #         return None

    #     if not self.stack:
    #         # nothing to convert
    #         return None

    #     # pop the value we're converting (so it's consumed once)
    #     stack_val = self.stack.pop()
    #     # unwrap Var -> name string if needed
    #     if isinstance(stack_val, Var):
    #         base = stack_val.name
    #     else:
    #         base = str(stack_val)

    #     # build nested conversion: apply conversions in order they were pushed
    #     # so first pushed becomes inner, last pushed becomes outer
    #     expr = base
    #     for instr in self.conv_instr_stack:
    #         expr = Var(f"{instr}({expr})")

    #     # emit assignment once
    #     self.expr = emit_expr(Assign(target=Var(operand), expr=expr))
    #     self.output.append(self.expr)

    #     # clear conversion stack after it's consumed
    #     self.conv_instr_stack.clear()

    #     print(f"Final assignment: {self.expr}")
    #     self.expr = None
    #     return

    def convert(self, opcode: str, operand: str):    
        if opcode in ("A", "AN", "O", "ON", "A(", "O(", "AN(", "ON(", "SET", "CLR", "="):
            self.convert_bools(opcode=opcode, operand=operand)

        if opcode in ("ITD", "DTR"):
            conversion = conversion_instructions(opcode)
            self.conv_instr_stack.append(conversion)
    
        if opcode in ("L", "T") or opcode in arithmetic_operators or opcode in comparison_operators or opcode in conv_instructions:
            if opcode in arithmetic_operators:
                self.op = arithmetic_operators[opcode]
            if opcode in comparison_operators:
                self.op = comparison_operators[opcode]
            if self.op is None:
                if opcode == "T" and len(self.conv_instr_stack) >= 1:
                    self.convert_conv_instructions(opcode=opcode, operand=operand)
                else:
                    self.convert_transfers(opcode=opcode, operand=operand)
            else:
                self.convert_arithmetic_operators(opcode=opcode, op=self.op, operand=operand)
        

    def ret_output(self):
        self.close_region()
        return self.output

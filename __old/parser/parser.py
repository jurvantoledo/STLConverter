from dataclasses import dataclass
from typing import List, Optional

from parser.pretty_printer import Expr, GroupMarker, And, Or, Not, Lit, Num, Var, BinOp, CompOp, emit_expr
from parser.operators import arithmetic_ops, comparison_ops


# --- Conversion state ---
class STLConverter:
    def __init__(self):
        self.expr: Optional[Expr] = None            # For Boolean RLO logic
        self.bool_stack: List[GroupMarker] = []     # For boolean Grouping
        self.stack: List[Expr] = []                 # For arithmetic (like ACCU stack)
        self.out: List[str] = []                    # Output lines
        self.region_open: bool = False

        # pending_jump will be either None or a dict:
        # {"cond": Expr, "label": "MTGC", "saw_label": False}
        self.pending_jump = None
        self.pending_instructions: List[str] = []   # buffered assignments (strings)
    
        self.pending_flank = None

    # Boolean helpers
    def push_and(self, x: Expr): self.expr = x if self.expr is None else And(self.expr, x)
    def push_or(self, x: Expr): self.expr = x if self.expr is None else Or(self.expr, x)
    
    # Data helpers
    def push_load(self, operand: str):
        try:
            self.stack.append(Num(operand))
        except ValueError:
            try:
                self.stack.append(Var(operand))
            except ValueError:
                print(f"Cant append operand {operand} to stack")

    def apply_binop(self, op_symbol: str):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(BinOp(op=op_symbol, a=a, b=b))
        return

    def apply_comparison(self, op_symbol: str):
        b = self.stack.pop()
        a = self.stack.pop()
        self.expr = CompOp(op=op_symbol, a=a, b=b)  # boolean RLO
    
    def store(self, dest: str):
        """
        Always use store(...) as the single place to produce/buffer assignments.
        If a pending_jump exists, buffer; otherwise emit directly.
        """
        if self.stack:
            val = self.stack[-1]  # peek
            assignment = f"{dest} := {emit_expr(val)};"
            if self.pending_jump is not None:
                self.pending_instructions.append(assignment)
            else:
                self.out.append(f"\t{assignment}\n")
        
        # Emit special boolean assignment IF/ELSE only when not inside a pending jump.
        if self.expr and self.pending_jump is None:
            cond = emit_expr(self.expr)
            self.out.append(
                f"\tIF {cond} THEN\n\t\t{dest} := true\n\tELSE\n\t\t{dest} := false\n\tEND_IF\n"
            )
            self.expr = None
    
    def close_region(self):
        if self.region_open:
            self.out.append(f"END_REGION\n\n")
            self.region_open = False

    # Helper to flush the buffered pending_instructions under the pending condition
    def _flush_pending_jump(self):
        if not self.pending_jump:
            return
        cond_expr = self.pending_jump["cond"]
        # If there are no buffered instructions, don't produce an empty IF block.
        if self.pending_instructions:
            self.out.append(f"\tIF {emit_expr(cond_expr)} THEN\n")
            for instr in self.pending_instructions:
                # indent the buffered assignment
                self.out.append(f"\t\t{instr}\n")
            self.out.append("\tEND_IF\n\n")
        # clear pending state
        self.pending_instructions.clear()
        self.pending_jump = None

    # Main dispatcher
    def handle(self, opcode: str, operand: Optional[str] = None, stl_type: Optional[str] = None, stl_value: Optional[str] = None):
        if stl_type == "TITLE":
            self.close_region()
            self.out.append(f'REGION "{stl_value}"\n')
            self.region_open = True
            self.expr = None
            self.stack.clear()
            return
        
        # LABEL handling: when we see the label that matches a pending jump,
        # we do NOT flush immediately. Instead mark that we've seen the label,
        # so the next instruction(s) after the label are captured.
        if stl_type == "LABEL":
            label_name = opcode.rstrip(":")
            if self.pending_jump and self.pending_jump["label"] == label_name:
                # mark that we have seen the label; waiting to capture next instructions
                self.pending_jump["saw_label"] = True
                # do not flush here — the instruction to buffer is after the label
            return
        # If there's a pending jump:
        # - if we haven't seen the label yet, we still accept loads/comparisons (if they appear),
        #   but typically the instruction will be after the label in the STL you provided.
        # - if we have seen the label (saw_label == True), we want to allow the next T (store)
        #   to be processed by `store()` so it gets buffered (store buffers when pending_jump != None).
        if self.pending_jump:
            # Before label has been seen: allow loads/comparisons to build expr if present (rare case)
            if not self.pending_jump.get("saw_label", False):
                if opcode == "L":
                    self.push_load(operand)
                    return
                if opcode in comparison_ops:
                    self.apply_comparison(comparison_ops[opcode])
                    return
                # otherwise ignore other ops while waiting for label
                return
            else:
                # We have seen the matching label, so the *next* meaningful instruction(s)
                # should be captured by store/push_load/etc.  Let normal handlers process them,
                # so do NOT return early here (except handle explicit L/comparison which we forward).
                if opcode == "L":
                    self.push_load(operand)
                    return
                if opcode in comparison_ops:
                    self.apply_comparison(comparison_ops[opcode])
                    return
                # important: do NOT intercept T here. Let handle_operators -> store(...) be called,
                # because store() will buffer the assignment (pending_jump is still set).
                # After we processed T (and it buffered), we should flush.
                # We'll detect and flush below after normal processing.
                # So do not `return` here; fallthrough to the normal handlers.
        
        # groups
        if opcode in ("A(", "O(", ")"):
            self.handle_group(opcode=opcode)
            return

        # booleans
        if opcode in ("A", "AN", "O", "ON", "SET", "CLR", "="):
            self.handle_bool(opcode=opcode, operand=operand)
            # After handle_bool we might have stored something; if it was buffered under a pending jump
            # and we've already seen the label, we might want to flush — handled after main ops.
            return
        
        if opcode in ("FP", "FN"):
            self.handle_flank(opcode=opcode, operand=operand)
            return

        # Data / arithmetic / comparison
        if opcode in arithmetic_ops or opcode in comparison_ops or opcode in ("L", "T"):
            self.handle_operators(opcode=opcode, operand=operand)
            # If a pending_jump was active and we had already seen the label, and the operator was T,
            # `store` buffered the assignment. So flush now (only if saw_label True).
            if self.pending_jump and self.pending_jump.get("saw_label", False):
                # flush buffered assignments under IF, then clear pending
                self._flush_pending_jump()
            return

        # Jump condition (JC/JCN)
        if opcode in ("JC", "JCN"):
            # stl_type should be "JUMP"
            if stl_type == "JUMP":
                if self.expr is None:
                    print(f"Warning: {opcode} without a boolean RLO; skipping jump to {operand}")
                    return
                cond = self.expr
                if opcode == "JCN":
                    cond = Not(self.expr)
                # set pending jump state; saw_label starts False
                self.pending_jump = {"cond": cond, "label": operand, "saw_label": False}
                # reset current RLO
                self.expr = None
            return
    
    # Boolean
    def handle_bool(self, opcode: str, operand: str):
        if opcode == "SET": 
            self.expr = Lit(True); return
        if opcode == "CLR": 
            self.expr = Lit(False); return
        if opcode == "A": 
            self.push_and(Var(operand)); return
        if opcode == "AN": 
            self.push_and(Not(Var(operand))); return
        if opcode == "O": 
            self.push_or(Var(operand)); return
        if opcode == "ON": 
            self.push_or(Not(Var(operand))); return
        if opcode == "=": 
            self.store(operand); return
    
    def handle_flank(self, opcode: str, operand: str):
        """
            Handle rising (FP) or falling (FN) edge detection.
            STL pattern:
                A <input>
                FP <helper>
                = <target>
            Becomes in SCL:
                IF <input> AND NOT <helper> THEN
                    <target> := true
                ELSE
                    <target> := false
                END_IF;
                <helper> := <input>;
        """
        # opcode is "FP" or "FN"; operand is helper var (e.g. "#FPhulp_TijdPuls")
        if self.expr is None:
            print(f"Warning {opcode} without input expression; skipping")
            return

        # Keep the original input expression object (not its string)
        original_input_expr = self.expr

        # Build the pulse expression for storage:
        if opcode == "FP":
            pulse_expr = And(original_input_expr, Not(Var(operand)))
        else:  # "FN"
            pulse_expr = And(Not(original_input_expr), Var(operand))

        # Replace current expr with pulse_expr so '=' will store it using existing store() logic
        self.expr = pulse_expr

        # Remember helper + original input so we can emit helper := input after the '=' store
        self._pending_flank = {"helper": operand, "input_expr": original_input_expr}
        return
    
    # Data / arithmetic / operators
    def handle_operators(self, opcode: str, operand: Optional[str]):
        if opcode == "L": 
            self.push_load(operand); return
        if opcode == "T": 
            self.store(operand); return
        if opcode in arithmetic_ops:
            self.apply_binop(arithmetic_ops[opcode])
        if opcode in comparison_ops:
            self.apply_comparison(comparison_ops[opcode])

    # Groups
    def handle_group(self, opcode: str):
        if opcode == "A(" or opcode == "A(;":
            self.bool_stack.append(GroupMarker("AND", self.expr))
            self.expr = None
        elif opcode == "O("or opcode == "O(;":
            self.bool_stack.append(GroupMarker("OR", self.expr))
        elif opcode == ")":
            gm = self.bool_stack.pop()
            group_expr = self.expr
            self.expr = gm.saved
            if gm.kind == "AND": 
                self.push_and(group_expr)
            else: 
                self.push_or(group_expr)

    def finish(self):
        # If we finish with a pending jump left open, attempt a flush (guarded)
        if self.pending_jump:
            self._flush_pending_jump()
        self.close_region()
        return self.out

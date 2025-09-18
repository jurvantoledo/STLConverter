arithmetic_operators = {
    "+I": "+", "-I": "-", "/I": "/", "*I": "*",
    "+D": "+", "-D": "-", "/D": "/", "*D": "*",
}

comparison_operators = {
    ">=I": ">=", ">I": ">", "==I": "==", "<=I": "<=", "<I": "<",
    ">=D": ">=", ">D": ">", "==D": "==", "<=D": "<=", "<D": "<",
}

conv_instructions = [
    "ITD", "DTR", "RND", "RND+", "RND-", "TRUNC", "TDI", "DTB", "BTD"
]

def conversion_instructions(instr):
    if instr == "ITD":
        return f"INT_TO_DINT"
    if instr == "DTR":
        return f"DINT_TO_REAL"
    return
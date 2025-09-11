from typing import List
from lexer import lexer
from parser import STLConverter

def fix_awl(file) -> tuple[List, List, List]:
    header = []
    body = []
    footer = []
    is_header = True

    for lines in file.read().splitlines():
        lines = lines.strip()
        if len(lines) == 0:
            continue

        if lines != "NETWORK" and is_header:
            header.append(lines)
            is_header = True
        else:
            is_header = False
        
        if not lines.startswith("BEGIN") and is_header == False and not lines.startswith("END_FUNCTION_BLOCK"):
            body.append(lines)
        if lines.startswith("END_FUNCTION_BLOCK") and is_header == False:
            footer.append(lines)

    return header, body, footer

def main():
    output = []
    with open("example.awl", 'r') as f:
        header, body, footer = fix_awl(f)

        tokenized = lexer(body)

        converter = STLConverter()

        for token in tokenized:
            token_type = token.get("type")
            token_value = token.get("value")

            opcode = token.get("opcode")
            operand = token.get("operand")
            
            converter.handle_networks(type=token_type, value=token_value)
            converter.handle_comment(type=token_type, value=token_value)
            converter.convert(opcode, operand)

        output = converter.ret_output()
    
    print(output)
    return 0

if __name__ == "__main__":
    main()
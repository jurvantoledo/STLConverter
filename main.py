from lexer.lexer import lexer
from parser.parser import STLConverter
from writer import writer

def split_awl(file: str) -> tuple[list, list, list]:
    header = []
    body = []
    footer = []
    in_body = False

    for line in file.splitlines():
        # If line = BEGIN added to header part and continue loop
        if line.strip() == "BEGIN":
            in_body = True
            header.append(line)
            continue
        # If line != BEGIN AND != END_FUNCTION add to body
        if not in_body:
            header.append(line)
        elif in_body and not line.strip().startswith("END_FUNCTION"):
            body.append(line)

        # If line = END_FUNCTION end line set body to false and continue loop
        if line.strip().startswith("END_FUNCTION"):
            footer.append(line)
            in_body = False
            continue
    
    return header, body, footer


def main() -> int:
    with open("example.awl") as f:
        header, body, footer = split_awl(f.read())

    tokenized = lexer(body=body)

    conv = STLConverter()

    for tokens in tokenized:
        stl_type = tokens.get("type")
        value = tokens.get("value")

        opcode = tokens.get("opcode")
        operand = tokens.get("operand")
        
        conv.handle(opcode=opcode, operand=operand, stl_type=stl_type, stl_value=value)
    
    result = conv.finish()

    writer(header=header, out=result, footer=footer)
    return 0

if __name__ == '__main__':
    main()


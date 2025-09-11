def lexer(body: list):
    tokenizer = [{}]
    for line in body:
        line = line.strip()
        if (len(line) == 0):
            continue

        if line.startswith("NETWORK"):
            tokenizer.append({"type": "NETWORK", "value": "REGION"})
        elif line.startswith("TITLE"):
            tokenizer.append({"type": "TITLE", "value": line.split("=")[1].strip()})
        else:
            separator = " "
            if line.find(separator) != -1:
                parts = line.split()
                if parts[0] == "JC" or parts[0] == "JCN":
                    tokenizer.append({"type": 'JUMP', 'opcode': parts[0], 'operand': parts[1].rstrip(";")})
                elif parts[0].endswith(":"):
                    tokenizer.append({"type": 'LABEL', 'opcode': parts[0], 'operand': None})
                    if len(parts) > 1:
                        opcode = parts[1]
                        operand = parts[2].rstrip(";") if len(parts) > 2 else None
                        tokenizer.append({"type": 'INSTRUCTION', 'opcode': opcode, 'operand': operand})
                else:
                    tokenizer.append({"type": 'INSTRUCTION', 'opcode': parts[0], 'operand': parts[1].rstrip(";")})
                continue
            else:
                if line.endswith(":"):
                    tokenizer.append({"type": 'LABEL', 'opcode': line, 'operand': None})
                else:
                    tokenizer.append({"type": 'INSTRUCTION', 'opcode': line.rstrip(";"), 'operand': None})
                continue
    print(tokenizer)
    return tokenizer


# L 0
# T Time
# time := 0
# var := val
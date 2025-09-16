from typing import List
def lexer(body: List):
    tokenized = []
    for text in body:
        if text.startswith("NETWORK"):
            tokenized.append({"type": "REGION", "value": text})
            continue
        if text.startswith("TITLE"):
            tokenized.append({"type": "TITLE", "value": text.split("=")[1].strip()})
            continue
        if text.startswith("//"):
            tokenized.append({'type': 'COMMENT', 'value': text})
        else:
            part = text.split(' ')
            if (len(part) >= 2):
                opcode = part[0]
                operand = part[1].rstrip(";")

                tokenized.append({"type": "INSTRUCTION", 'opcode': opcode, 'operand': operand})
                continue
            else:
                tokenized.append({"type": "INSTRUCTION", 'opcode': part[0].rstrip(";")})
    print(tokenized)
    return tokenized
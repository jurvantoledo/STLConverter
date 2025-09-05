from typing import List

def writer(header, out: List[str], footer) -> None:
    with open("example.scl", 'w+') as f:
        for line in header:
            modified = f"{line}\n"
            f.writelines(modified)
        f.writelines(out)
        f.writelines(footer)
        f.close()
    return None
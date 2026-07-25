import ast
from pathlib import Path


def chunk_python_file(code, file_path):
    """
    Takes the full code of one Python file (as a string)
    and splits it into function/class-level chunks.
    """
    chunks = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Could not parse {file_path}: {e}")
        return chunks

    lines = code.split("\n")

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):

            start_line = node.lineno
            end_line = node.end_lineno

            chunk_lines = lines[start_line - 1 : end_line]
            chunk_code = "\n".join(chunk_lines)

            chunk_type = "function" if isinstance(node, ast.FunctionDef) else "class"

            chunks.append({
                "file_path": str(file_path),
                "chunk_type": chunk_type,
                "name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "code": chunk_code,
            })

    return chunks


if __name__ == "__main__":
    sample_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

class Calculator:
    def multiply(self, a, b):
        return a * b
"""

    result = chunk_python_file(sample_code, "calculator.py")

    for chunk in result:
        print("=" * 50)
        print("Name:", chunk["name"])
        print("Type:", chunk["chunk_type"])
        print("Lines:", chunk["start_line"], "-", chunk["end_line"])
        print("Code:\n", chunk["code"])
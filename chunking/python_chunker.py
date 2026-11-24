import ast
from typing import Any, Dict, List, Optional


def chunk_python_file(code: str, file_path: str) -> List[Dict[str, Any]]:
    """
    Takes Python source code and splits it into structural chunks.
    Identifies:
      - Module-level logic (scripts with top-level assignments/calls)
      - Standalone functions (parent=None)
      - Classes (parent=None)
      - Class methods (tagged with parent=ClassName)
    """
    chunks: List[Dict[str, Any]] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Could not parse {file_path}: {e}")
        return chunks

    lines = code.split("\n")

    # 1. Check for module-level statements (logic outside any def or class)
    top_level_stmts = [
        stmt for stmt in tree.body
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom))
    ]
    # Filter out lone module docstring
    if top_level_stmts and isinstance(top_level_stmts[0], ast.Expr) and isinstance(top_level_stmts[0].value, ast.Constant) and isinstance(top_level_stmts[0].value.value, str):
        executable_top_level = top_level_stmts[1:]
    else:
        executable_top_level = top_level_stmts

    if executable_top_level:
        first_line = executable_top_level[0].lineno
        last_line = max(getattr(stmt, "end_lineno", stmt.lineno) for stmt in executable_top_level)
        mod_code = "\n".join(lines[first_line - 1 : last_line])
        chunks.append({
            "file_path": str(file_path),
            "chunk_type": "module",
            "name": "<module>",
            "parent": None,
            "start_line": first_line,
            "end_line": last_line,
            "code": mod_code,
        })

    # 2. Iterate top-level functions and classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            chunk_code = "\n".join(lines[start_line - 1 : end_line])
            chunks.append({
                "file_path": str(file_path),
                "chunk_type": "function",
                "name": node.name,
                "parent": None,
                "start_line": start_line,
                "end_line": end_line,
                "code": chunk_code,
            })

        elif isinstance(node, ast.ClassDef):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            class_code = "\n".join(lines[start_line - 1 : end_line])
            chunks.append({
                "file_path": str(file_path),
                "chunk_type": "class",
                "name": node.name,
                "parent": None,
                "start_line": start_line,
                "end_line": end_line,
                "code": class_code,
            })

            # Tag method chunks with their parent class name
            for class_item in node.body:
                if isinstance(class_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_start = class_item.lineno
                    m_end = getattr(class_item, "end_lineno", m_start)
                    m_code = "\n".join(lines[m_start - 1 : m_end])
                    chunks.append({
                        "file_path": str(file_path),
                        "chunk_type": "function",
                        "name": class_item.name,
                        "parent": node.name,
                        "start_line": m_start,
                        "end_line": m_end,
                        "code": m_code,
                    })

    return chunks
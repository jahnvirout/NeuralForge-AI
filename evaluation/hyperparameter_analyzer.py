import ast
from typing import Any, Dict, List, Set


TREE_MODEL_CLASSES = {
    "DecisionTreeClassifier",
    "DecisionTreeRegressor",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "ExtraTreeClassifier",
    "ExtraTreeRegressor",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "HistGradientBoostingClassifier",
    "HistGradientBoostingRegressor",
}

DEPTH_LIMITING_PARAMS = {
    "max_depth",
    "min_samples_leaf",
    "max_leaf_nodes",
}


def _get_call_name(node: ast.AST) -> str:
    """Extracts function or class name from a Call AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _get_evidence_snippet(code: str, start_line: int, end_line: int) -> str:
    """Extracts exact source code lines for a given range."""
    lines = code.splitlines()
    if 1 <= start_line <= len(lines):
        end_idx = min(end_line, len(lines))
        return "\n".join(lines[start_line - 1 : end_idx])
    return ""


def detect_risky_hyperparameters(code: str, file_path: str) -> List[Dict[str, Any]]:
    """
    AST-based hyperparameter risk analyzer.
    Detects tree-based models instantiated without bounding constraints
    such as max_depth, min_samples_leaf, or max_leaf_nodes.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    issues: List[Dict[str, Any]] = []

    # Map statements to enclosing scope
    parent_map: Dict[ast.AST, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                parent_map[child] = node.name

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        model_name = _get_call_name(node.func)
        if model_name in TREE_MODEL_CLASSES:
            # Check keyword arguments for depth or leaf constraints
            provided_kwargs: Set[str] = {
                kw.arg for kw in node.keywords if kw.arg is not None
            }

            has_constraint = bool(provided_kwargs.intersection(DEPTH_LIMITING_PARAMS))

            if not has_constraint:
                scope_name = parent_map.get(node, "<module>")
                snippet = _get_evidence_snippet(
                    code,
                    node.lineno,
                    getattr(node, "end_lineno", node.lineno),
                )
                issues.append({
                    "file": file_path,
                    "function": scope_name,
                    "line": node.lineno,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "severity": "medium",
                    "issue": f"{model_name} initialized without max_depth — tree can grow unbounded, risking overfitting",
                    "why_it_matters": (
                        "Tree models with unconstrained depth can grow until every training sample is "
                        "isolated into a leaf, leading to extreme variance and degraded generalization."
                    ),
                    "evidence_snippet": snippet or f"{model_name}() instantiated without max_depth",
                    "suggestion": f"Set max_depth (e.g. max_depth=5) or min_samples_leaf in {model_name} to constrain tree complexity.",
                    "confidence": "high",
                })

    return issues


def scan_repository_for_hyperparameter_risk(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs hyperparameter risk check across all repository files."""
    all_issues: List[Dict[str, Any]] = []
    for file_info in files:
        if file_info.get("language") == "Python":
            issues = detect_risky_hyperparameters(
                file_info["code"],
                file_info["relative_path"],
            )
            all_issues.extend(issues)
    return all_issues
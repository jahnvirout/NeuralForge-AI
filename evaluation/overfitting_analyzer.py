import ast
from typing import Any, Dict, List, Set


METRIC_FUNCTIONS = {
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc_score",
    "mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    "classification_report",
    "confusion_matrix",
    "cross_val_score",
    "cross_validate",
    "validation_curve",
    "learning_curve",
}

EVAL_METHOD_NAMES = {"score", "evaluate", "predict", "predict_proba"}
NON_ESTIMATOR_CLASSES = {
    "StandardScaler",
    "MinMaxScaler",
    "RobustScaler",
    "OneHotEncoder",
    "OrdinalEncoder",
    "SimpleImputer",
    "PCA",
    "TfidfVectorizer",
    "CountVectorizer",
}


def _get_call_name(node: ast.AST) -> str:
    """Extracts function or method name from a Call AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _extract_var_names(node: ast.AST) -> Set[str]:
    """Recursively extracts all variable names referenced in an expression."""
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
    return names


def _get_evidence_snippet(code: str, start_line: int, end_line: int) -> str:
    """Extracts exact source code lines for a given range."""
    lines = code.splitlines()
    if 1 <= start_line <= len(lines):
        end_idx = min(end_line, len(lines))
        return "\n".join(lines[start_line - 1 : end_idx])
    return ""


def detect_no_validation(code: str, file_path: str) -> List[Dict[str, Any]]:
    """
    AST-based overfitting detector.
    Flags model estimators trained via .fit() that lack corresponding validation,
    cross-validation, or held-out test evaluation in the same scope or file.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    issues: List[Dict[str, Any]] = []

    # First check: does the file contain global cross-validation or evaluation tools?
    file_has_cv = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _get_call_name(node.func)
            if name in {"cross_val_score", "cross_validate", "GridSearchCV", "RandomizedSearchCV"}:
                file_has_cv = True
                break

    if file_has_cv:
        return []

    # Collect scopes: module body and function bodies
    scopes: List[tuple[str, List[ast.stmt]]] = [("<module>", tree.body)]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scopes.append((node.name, node.body))

    for scope_name, statements in scopes:
        fit_calls: List[ast.Call] = []
        has_validation = False
        non_estimator_vars: Set[str] = set()

        for stmt in statements:
            # Track preprocessors so their .fit() is not mistaken for model training
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                inst_name = _get_call_name(stmt.value.func)
                if inst_name in NON_ESTIMATOR_CLASSES:
                    for target in stmt.targets:
                        non_estimator_vars.update(_extract_var_names(target))

            for child in ast.walk(stmt):
                if not isinstance(child, ast.Call):
                    continue

                call_name = _get_call_name(child.func)

                # Check for explicit metric evaluation function
                if call_name in METRIC_FUNCTIONS:
                    has_validation = True

                # Check for .score(), .evaluate(), or .predict() on validation/test data
                if call_name in EVAL_METHOD_NAMES:
                    call_args = set()
                    for arg in child.args:
                        call_args.update(_extract_var_names(arg))
                    for kw in child.keywords:
                        call_args.update(_extract_var_names(kw.value))

                    # Check if evaluation targets a test/val variable
                    test_like = any(
                        any(token in v.lower() for token in ["test", "val", "holdout", "eval"])
                        for v in call_args
                    )
                    # .score() with 2+ arguments is inherently an evaluation call
                    if test_like or (call_name in {"score", "evaluate"} and len(child.args) >= 2):
                        has_validation = True

                # Check for .fit() call on estimator
                if call_name == "fit" and isinstance(child.func, ast.Attribute):
                    caller_name = _get_call_name(child.func.value)
                    # Skip known preprocessor instances
                    if caller_name not in non_estimator_vars:
                        # Model estimators typically fit on (X, y) or (X_train, y_train)
                        fit_calls.append(child)

        # If models were fitted in this scope but no validation occurred
        if fit_calls and not has_validation:
            for fit_node in fit_calls:
                snippet = _get_evidence_snippet(
                    code,
                    fit_node.lineno,
                    getattr(fit_node, "end_lineno", fit_node.lineno),
                )
                issues.append({
                    "file": file_path,
                    "function": scope_name,
                    "line": fit_node.lineno,
                    "start_line": fit_node.lineno,
                    "end_line": getattr(fit_node, "end_lineno", fit_node.lineno),
                    "severity": "medium",
                    "issue": "Model is trained but never evaluated on a validation/test set",
                    "why_it_matters": (
                        "Training a model without held-out validation or cross-validation leaves "
                        "overfitting and generalizability risks undetected."
                    ),
                    "evidence_snippet": snippet or "model.fit(...) called without subsequent evaluation",
                    "suggestion": "Add a train/validation split and evaluate performance (e.g. accuracy, score) on held-out data.",
                    "confidence": "high",
                })

    return issues


def scan_repository_for_overfitting_risk(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs overfitting risk check across all repository files."""
    all_issues: List[Dict[str, Any]] = []
    for file_info in files:
        if file_info.get("language") == "Python":
            issues = detect_no_validation(
                file_info["code"],
                file_info["relative_path"],
            )
            all_issues.extend(issues)
    return all_issues
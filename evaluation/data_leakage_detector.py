import ast
from typing import Any, Dict, List, Optional, Set


PREPROCESSOR_CLASSES = {
    "StandardScaler",
    "MinMaxScaler",
    "RobustScaler",
    "MaxAbsScaler",
    "Normalizer",
    "Binarizer",
    "OneHotEncoder",
    "OrdinalEncoder",
    "LabelEncoder",
    "TargetEncoder",
    "SimpleImputer",
    "KNNImputer",
    "IterativeImputer",
    "PCA",
    "TruncatedSVD",
    "FastICA",
    "KernelPCA",
    "SelectKBest",
    "SelectPercentile",
    "RFE",
    "RFECV",
    "TfidfVectorizer",
    "CountVectorizer",
    "HashingVectorizer",
    "QuantileTransformer",
    "PowerTransformer",
    "KBinsDiscretizer",
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


def detect_scaling_before_split(code: str, file_path: str) -> List[Dict[str, Any]]:
    """
    AST-based scope-aware data leakage detector.
    Tracks whether data passed to fit or fit_transform of a scaler/transformer
    subsequently flows into train_test_split within the same scope.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    issues: List[Dict[str, Any]] = []

    # Collect scopes: module body and function bodies
    scopes: List[tuple[str, List[ast.stmt]]] = [("<module>", tree.body)]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scopes.append((node.name, node.body))

    for scope_name, statements in scopes:
        # Preprocessor instances in this scope
        preprocessor_vars: Set[str] = set()
        # Variables that have been fitted prior to a split
        tainted_vars: Set[str] = set()
        # Mapping of variable -> lineno where fit/fit_transform occurred
        fit_call_info: Dict[str, ast.Call] = {}
        # Variables produced by a valid split (e.g. X_train, X_test)
        split_vars: Set[str] = set()

        for stmt in statements:
            # Detect pipeline instantiation (safe, avoids manual leakage)
            for child in ast.walk(stmt):
                if isinstance(child, ast.Call):
                    call_name = _get_call_name(child.func)
                    if call_name in {"Pipeline", "make_pipeline"}:
                        # Pipeline handles train-only fitting during CV
                        pass

            # Detect preprocessor variable assignments
            # e.g., scaler = StandardScaler()
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Call):
                    call_name = _get_call_name(stmt.value.func)
                    if call_name in PREPROCESSOR_CLASSES:
                        for target in stmt.targets:
                            preprocessor_vars.update(_extract_var_names(target))

            # Inspect calls inside this statement
            for child in ast.walk(stmt):
                if not isinstance(child, ast.Call):
                    continue

                call_name = _get_call_name(child.func)

                # Check for train_test_split call
                if call_name == "train_test_split":
                    arg_vars: Set[str] = set()
                    for arg in child.args:
                        arg_vars.update(_extract_var_names(arg))

                    # If assigning: X_train, X_test, y_train, y_test = train_test_split(...)
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            split_vars.update(_extract_var_names(target))

                    # Check if any input to train_test_split was tainted by fit/fit_transform
                    leaked = arg_vars.intersection(tainted_vars)
                    if leaked:
                        for var in leaked:
                            fit_call = fit_call_info.get(var, child)
                            snippet = _get_evidence_snippet(
                                code,
                                fit_call.lineno,
                                getattr(child, "end_lineno", child.lineno),
                            )
                            issues.append({
                                "file": file_path,
                                "function": scope_name,
                                "line": fit_call.lineno,
                                "start_line": fit_call.lineno,
                                "end_line": getattr(fit_call, "end_lineno", fit_call.lineno),
                                "severity": "high",
                                "issue": f"Possible data leakage: preprocessor fit on '{var}' before train_test_split()",
                                "why_it_matters": (
                                    "Fitting transformations on the dataset before splitting leaks test "
                                    "distribution statistics into the training pipeline, leading to overly "
                                    "optimistic validation results."
                                ),
                                "evidence_snippet": snippet or f"{var} transformed before split",
                                "suggestion": "Split data into train and test sets first, then fit preprocessors solely on training data.",
                                "confidence": "high",
                            })
                    continue

                # Check for fit_transform or fit calls on preprocessors
                is_fit_transform = call_name == "fit_transform"
                is_preproc_fit = (
                    call_name == "fit"
                    and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id in preprocessor_vars
                )

                if is_fit_transform or is_preproc_fit:
                    # Check what arguments were passed
                    input_args: Set[str] = set()
                    for arg in child.args:
                        input_args.update(_extract_var_names(arg))

                    # If input is already a training split variable (e.g. X_train), safe!
                    if input_args and input_args.issubset(split_vars):
                        continue

                    # Otherwise, taint the input variables and any output target
                    for v in input_args:
                        tainted_vars.add(v)
                        fit_call_info[v] = child

                    # If result is assigned to variable(s), taint them too:
                    # e.g., X_scaled = scaler.fit_transform(X)
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            for out_v in _extract_var_names(target):
                                tainted_vars.add(out_v)
                                fit_call_info[out_v] = child

    return issues


def scan_repository_for_leakage(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs data leakage check across all repository files."""
    all_issues: List[Dict[str, Any]] = []
    for file_info in files:
        if file_info.get("language") == "Python":
            issues = detect_scaling_before_split(
                file_info["code"],
                file_info["relative_path"],
            )
            all_issues.extend(issues)
    return all_issues
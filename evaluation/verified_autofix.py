import ast
import difflib
import re
from typing import Any, Dict, List, Optional

from evaluation.data_leakage_detector import detect_scaling_before_split


def validate_fix_variables(
    patched_code: str,
    assigned_by_fix: set,
    split_vars: set,
    fix_end_line: int,
) -> bool:
    """
    Validates that every name assigned by the fix is either:
    1. A pre-existing split variable, OR
    2. Referenced later in the patched code.
    Returns False if any newly created variable is never used later.
    """
    try:
        tree = ast.parse(patched_code)
    except SyntaxError:
        return False

    newly_created = assigned_by_fix - split_vars
    if not newly_created:
        return True

    referenced_later = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            lineno = getattr(node, "lineno", 0)
            if lineno > fix_end_line:
                referenced_later.add(node.id)

    for var in newly_created:
        if var not in referenced_later:
            return False

    return True


def generate_verified_leakage_fix(
    code: str, file_path: str, _assign_new_vars: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Deterministically generates a unified-diff auto-fix for preprocessor data leakage.
    Steps:
      1. Reorders dataset splitting before feature scaling.
      2. Reassigns original split variable names in-place on training and test sets.
      3. Validates patch by in-memory AST parse, detector re-analysis, and unused variable check.
      4. Returns fix only if all checks pass.
    NEVER executes repo code.
    """
    initial_issues = detect_scaling_before_split(code, file_path)
    if not initial_issues:
        return None

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    fit_node = None
    split_node = None
    scaled_var = None
    preproc_obj = None
    raw_var = None
    train_var = None
    test_var = None
    split_vars = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Match: var_scaled = preproc.fit_transform(var_raw)
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr == "fit_transform" and len(node.value.args) >= 1:
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                        if isinstance(node.value.func.value, ast.Name) and isinstance(node.value.args[0], ast.Name):
                            if fit_node is None:
                                fit_node = node
                                scaled_var = node.targets[0].id
                                preproc_obj = node.value.func.value.id
                                raw_var = node.value.args[0].id

            # Match: X_train, X_test, ... = train_test_split(...)
            if isinstance(node.value, ast.Call):
                call_name = ""
                if isinstance(node.value.func, ast.Name):
                    call_name = node.value.func.id
                elif isinstance(node.value.func, ast.Attribute):
                    call_name = node.value.func.attr

                if call_name == "train_test_split" and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) >= 2:
                        if split_node is None:
                            split_node = node
                            if isinstance(target.elts[0], ast.Name):
                                train_var = target.elts[0].id
                            if isinstance(target.elts[1], ast.Name):
                                test_var = target.elts[1].id
                            split_vars = {
                                elt.id for elt in target.elts if isinstance(elt, ast.Name)
                            }

    if not fit_node or not split_node or fit_node.lineno >= split_node.lineno:
        return None

    if not scaled_var or not raw_var or not train_var or not test_var or not preproc_obj:
        return None

    # Verify scaled_var was passed to train_test_split
    arg_ids = [arg.id for arg in split_node.value.args if isinstance(arg, ast.Name)]
    if scaled_var not in arg_ids:
        return None

    lines = code.splitlines()
    fit_line_idx = fit_node.lineno - 1
    split_line_idx = split_node.lineno - 1

    # 1. Modify split line: replace scaled_var with raw_var (handles 2-way and 4-way splits)
    split_line = lines[split_line_idx]
    split_line_patched = re.sub(rf"\b{re.escape(scaled_var)}\b", raw_var, split_line)
    indent = re.match(r"^\s*", split_line).group()

    # 2. Build replacement block
    if _assign_new_vars:
        replacement_block = [
            split_line_patched,
            f"{indent}# Fit transformer strictly on training data",
            f"{indent}{scaled_var}_train = {preproc_obj}.fit_transform({train_var})",
            f"{indent}{scaled_var}_test = {preproc_obj}.transform({test_var})",
        ]
        assigned_by_fix = {f"{scaled_var}_train", f"{scaled_var}_test"}
    else:
        # Reassign ORIGINAL split variable names in-place so downstream code uses scaled data
        replacement_block = [
            split_line_patched,
            f"{indent}# Fit transformer strictly on training data",
            f"{indent}{train_var} = {preproc_obj}.fit_transform({train_var})",
            f"{indent}{test_var} = {preproc_obj}.transform({test_var})",
        ]
        assigned_by_fix = {train_var, test_var}

    # 3. Assemble patched code
    patched_lines = list(lines)
    patched_lines.pop(split_line_idx)
    patched_lines.pop(fit_line_idx)
    target_pos = split_line_idx - 1
    for offset, new_line in enumerate(replacement_block):
        patched_lines.insert(target_pos + offset, new_line)

    patched_code = "\n".join(patched_lines) + "\n"
    fix_end_line = target_pos + len(replacement_block)

    # --- IN-MEMORY RE-ANALYSIS VERIFICATION ---
    # 1. AST parse check
    try:
        ast.parse(patched_code)
    except SyntaxError:
        return None

    # 2. Detector re-analysis check
    recheck_issues = detect_scaling_before_split(patched_code, file_path)
    if len(recheck_issues) > 0:
        return None

    # 3. Fix variable usage check: newly created variables must be referenced later
    if not validate_fix_variables(patched_code, assigned_by_fix, split_vars, fix_end_line):
        return None

    # 4. Generate unified diff
    orig_lines_with_nl = [l + "\n" for l in lines]
    patched_lines_with_nl = [l + "\n" for l in patched_lines]
    diff = list(
        difflib.unified_diff(
            orig_lines_with_nl,
            patched_lines_with_nl,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )
    diff_text = "".join(diff)

    status_label = "leakage pattern removed (re-analysis + ast.parse passed); semantic equivalence not guaranteed"
    explanation = (
        "Split the dataset prior to feature transformation. "
        f"Fitted {preproc_obj} exclusively on {train_var}, and applied {preproc_obj}.transform({test_var}) "
        "to prevent test set distribution leakage. Validated via in-memory AST re-analysis. "
        "Caveat: leakage pattern removed (re-analysis + ast.parse passed); semantic equivalence not guaranteed."
    )

    return {
        "file": file_path,
        "verified": True,
        "status": status_label,
        "diff": diff_text,
        "patched_code": patched_code,
        "explanation": explanation,
    }


def generate_all_verified_fixes(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs verified auto-fix generator for all Python files in the repository."""
    verified_fixes: List[Dict[str, Any]] = []
    for file_info in files:
        if file_info.get("language") == "Python":
            fix = generate_verified_leakage_fix(file_info["code"], file_info["relative_path"])
            if fix is not None:
                verified_fixes.append(fix)
    return verified_fixes
